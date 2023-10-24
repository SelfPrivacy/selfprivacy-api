"""Generic handler for moving services"""

from __future__ import annotations
import subprocess
import time
import pathlib
import shutil

from pydantic import BaseModel
from selfprivacy_api.jobs import Job, JobStatus, Jobs
from selfprivacy_api.utils.huey import huey
from selfprivacy_api.utils.block_devices import BlockDevice
from selfprivacy_api.utils import ReadUserData, WriteUserData
from selfprivacy_api.services.service import Service, ServiceStatus
from selfprivacy_api.services.owned_path import OwnedPath


class FolderMoveNames(BaseModel):
    name: str
    bind_location: str
    owner: str
    group: str

    @staticmethod
    def from_owned_path(path: OwnedPath) -> FolderMoveNames:
        return FolderMoveNames(
            name=FolderMoveNames.get_foldername(path.path),
            bind_location=path.path,
            owner=path.owner,
            group=path.group,
        )

    @staticmethod
    def get_foldername(path: str) -> str:
        return path.split("/")[-1]

    @staticmethod
    def default_foldermoves(service: Service) -> list[FolderMoveNames]:
        return [
            FolderMoveNames.from_owned_path(folder)
            for folder in service.get_owned_folders()
        ]


@huey.task()
def move_service(
    service: Service,
    volume: BlockDevice,
    job: Job,
    folder_names: list[FolderMoveNames],
    userdata_location: str,
):
    """Move a service to another volume."""
    job = Jobs.update(
        job=job,
        status_text="Performing pre-move checks...",
        status=JobStatus.RUNNING,
    )
    service_name = service.get_display_name()
    with ReadUserData() as user_data:
        if not user_data.get("useBinds", False):
            Jobs.update(
                job=job,
                status=JobStatus.ERROR,
                error="Server is not using binds.",
            )
            return
    # Check if we are on the same volume
    old_volume = service.get_drive()
    if old_volume == volume.name:
        Jobs.update(
            job=job,
            status=JobStatus.ERROR,
            error=f"{service_name} is already on this volume.",
        )
        return
    # Check if there is enough space on the new volume
    if int(volume.fsavail) < service.get_storage_usage():
        Jobs.update(
            job=job,
            status=JobStatus.ERROR,
            error="Not enough space on the new volume.",
        )
        return
    # Make sure the volume is mounted
    if not volume.is_root() and f"/volumes/{volume.name}" not in volume.mountpoints:
        Jobs.update(
            job=job,
            status=JobStatus.ERROR,
            error="Volume is not mounted.",
        )
        return
    # Make sure current actual directory exists and if its user and group are correct
    for folder in folder_names:
        if not pathlib.Path(f"/volumes/{old_volume}/{folder.name}").exists():
            Jobs.update(
                job=job,
                status=JobStatus.ERROR,
                error=f"{service_name} is not found.",
            )
            return
        if not pathlib.Path(f"/volumes/{old_volume}/{folder.name}").is_dir():
            Jobs.update(
                job=job,
                status=JobStatus.ERROR,
                error=f"{service_name} is not a directory.",
            )
            return
        if (
            not pathlib.Path(f"/volumes/{old_volume}/{folder.name}").owner()
            == folder.owner
        ):
            Jobs.update(
                job=job,
                status=JobStatus.ERROR,
                error=f"{service_name} owner is not {folder.owner}.",
            )
            return

    # Stop service
    Jobs.update(
        job=job,
        status=JobStatus.RUNNING,
        status_text=f"Stopping {service_name}...",
        progress=5,
    )
    service.stop()
    # Wait for the service to stop, check every second
    # If it does not stop in 30 seconds, abort
    for _ in range(30):
        if service.get_status() not in (
            ServiceStatus.ACTIVATING,
            ServiceStatus.DEACTIVATING,
        ):
            break
        time.sleep(1)
    else:
        Jobs.update(
            job=job,
            status=JobStatus.ERROR,
            error=f"{service_name} did not stop in 30 seconds.",
        )
        return

    # Unmount old volume
    Jobs.update(
        job=job,
        status_text="Unmounting old folder...",
        status=JobStatus.RUNNING,
        progress=10,
    )
    for folder in folder_names:
        try:
            subprocess.run(
                ["umount", folder.bind_location],
                check=True,
            )
        except subprocess.CalledProcessError:
            Jobs.update(
                job=job,
                status=JobStatus.ERROR,
                error="Unable to unmount old volume.",
            )
            return
    # Move data to new volume and set correct permissions
    Jobs.update(
        job=job,
        status_text="Moving data to new volume...",
        status=JobStatus.RUNNING,
        progress=20,
    )
    current_progress = 20
    folder_percentage = 50 // len(folder_names)
    for folder in folder_names:
        shutil.move(
            f"/volumes/{old_volume}/{folder.name}",
            f"/volumes/{volume.name}/{folder.name}",
        )
        Jobs.update(
            job=job,
            status_text="Moving data to new volume...",
            status=JobStatus.RUNNING,
            progress=current_progress + folder_percentage,
        )

    Jobs.update(
        job=job,
        status_text=f"Making sure {service_name} owns its files...",
        status=JobStatus.RUNNING,
        progress=70,
    )
    for folder in folder_names:
        try:
            subprocess.run(
                [
                    "chown",
                    "-R",
                    f"{folder.owner}:{folder.group}",
                    f"/volumes/{volume.name}/{folder.name}",
                ],
                check=True,
            )
        except subprocess.CalledProcessError as error:
            print(error.output)
            Jobs.update(
                job=job,
                status=JobStatus.RUNNING,
                error=f"Unable to set ownership of new volume. {service_name} may not be able to access its files. Continuing anyway.",
            )

    # Mount new volume
    Jobs.update(
        job=job,
        status_text=f"Mounting {service_name} data...",
        status=JobStatus.RUNNING,
        progress=90,
    )

    for folder in folder_names:
        try:
            subprocess.run(
                [
                    "mount",
                    "--bind",
                    f"/volumes/{volume.name}/{folder.name}",
                    folder.bind_location,
                ],
                check=True,
            )
        except subprocess.CalledProcessError as error:
            print(error.output)
            Jobs.update(
                job=job,
                status=JobStatus.ERROR,
                error="Unable to mount new volume.",
            )
            return

    # Update userdata
    Jobs.update(
        job=job,
        status_text="Finishing move...",
        status=JobStatus.RUNNING,
        progress=95,
    )
    with WriteUserData() as user_data:
        if userdata_location not in user_data:
            user_data[userdata_location] = {}
        user_data[userdata_location]["location"] = volume.name
    # Start service
    service.start()
    Jobs.update(
        job=job,
        status=JobStatus.FINISHED,
        result=f"{service_name} moved successfully.",
        status_text=f"Starting {service_name}...",
        progress=100,
    )
