"""Generic handler for moving services"""

from __future__ import annotations
import subprocess
import pathlib
import shutil
from typing import List

from pydantic import BaseModel
from selfprivacy_api.jobs import Job, JobStatus, Jobs
from selfprivacy_api.utils.huey import huey
from selfprivacy_api.utils.block_devices import BlockDevice
from selfprivacy_api.utils import ReadUserData, WriteUserData
from selfprivacy_api.services.service import Service
from selfprivacy_api.services.owned_path import OwnedPath

from selfprivacy_api.services.service import StoppedService


class MoveError(Exception):
    """Move failed"""


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
    new_volume: BlockDevice,
    job: Job,
    folder_names: List[FolderMoveNames],
    userdata_location: str = None,  # deprecated, not used
):
    """
    Move a service to another volume.
    Is not allowed to raise errors because it is a task.
    """
    service_name = service.get_display_name()
    old_volume = service.get_drive()
    report_progress(0, job, "Performing pre-move checks...")

    try:
        with ReadUserData() as user_data:
            if not user_data.get("useBinds", False):
                raise MoveError("Server is not using binds.")

        check_volume(new_volume, service)
        check_folders(old_volume, folder_names)

        report_progress(5, job, f"Stopping {service_name}...")

        with StoppedService(service):
            report_progress(10, job, "Unmounting folders from old volume...")
            unmount_old_volume(folder_names)

            report_progress(20, job, "Moving data to new volume...")
            move_folders_to_volume(folder_names, old_volume, new_volume, job)

            report_progress(70, job, f"Making sure {service_name} owns its files...")
            chown_folders(folder_names, new_volume, job, service)

            report_progress(90, job, f"Mounting {service_name} data...")
            mount_folders(folder_names, new_volume)

            report_progress(95, job, f"Finishing moving {service_name}...")
            update_volume_in_userdata(service, new_volume)

            Jobs.update(
                job=job,
                status=JobStatus.FINISHED,
                result=f"{service_name} moved successfully.",
                status_text=f"Starting {service_name}...",
                progress=100,
            )
    except Exception as e:
        Jobs.update(
            job=job,
            status=JobStatus.ERROR,
            error=type(e).__name__ + " " + str(e),
        )


def check_volume(new_volume: BlockDevice, service: Service) -> bool:
    service_name = service.get_display_name()
    old_volume_name: str = service.get_drive()

    # Check if we are on the same volume
    if old_volume_name == new_volume.name:
        raise MoveError(f"{service_name} is already on volume {new_volume}")

    # Check if there is enough space on the new volume
    if int(new_volume.fsavail) < service.get_storage_usage():
        raise MoveError("Not enough space on the new volume.")

    # Make sure the volume is mounted
    if (
        not new_volume.is_root()
        and f"/volumes/{new_volume.name}" not in new_volume.mountpoints
    ):
        raise MoveError("Volume is not mounted.")


def check_folders(old_volume: BlockDevice, folder_names: List[FolderMoveNames]) -> None:
    # Make sure current actual directory exists and if its user and group are correct
    for folder in folder_names:
        path = pathlib.Path(f"/volumes/{old_volume}/{folder.name}")

        if not path.exists():
            raise MoveError(f"{path} is not found.")
        if not path.is_dir():
            raise MoveError(f"{path} is not a directory.")
        if path.owner() != folder.owner:
            raise MoveError(f"{path} owner is not {folder.owner}.")


def unmount_old_volume(folder_names: List[FolderMoveNames]) -> None:
    for folder in folder_names:
        try:
            subprocess.run(
                ["umount", folder.bind_location],
                check=True,
            )
        except subprocess.CalledProcessError:
            raise MoveError("Unable to unmount old volume.")


def move_folders_to_volume(
    folder_names: List[FolderMoveNames],
    old_volume: BlockDevice,
    new_volume: BlockDevice,
    job: Job,
) -> None:
    # Move data to new volume and set correct permissions
    current_progress = job.progress
    folder_percentage = 50 // len(folder_names)
    for folder in folder_names:
        shutil.move(
            f"/volumes/{old_volume}/{folder.name}",
            f"/volumes/{new_volume.name}/{folder.name}",
        )
        progress = current_progress + folder_percentage
        report_progress(progress, job, "Moving data to new volume...")


def chown_folders(
    folder_names: List[FolderMoveNames], volume: BlockDevice, job: Job, service: Service
) -> None:
    service_name = service.get_display_name()
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


def mount_folders(folder_names: List[FolderMoveNames], volume: BlockDevice) -> None:
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
            raise MoveError(f"Unable to mount new volume:{error.output}")


def update_volume_in_userdata(service: Service, volume: BlockDevice):
    with WriteUserData() as user_data:
        service_id = service.get_id()
        if "modules" not in user_data:
            user_data["modules"] = {}
        if service_id not in user_data["modules"]:
            user_data["modules"][service_id] = {}
        user_data["modules"][service_id]["location"] = volume.name


def report_progress(progress: int, job: Job, status_text: str) -> None:
    Jobs.update(
        job=job,
        status=JobStatus.RUNNING,
        status_text=status_text,
        progress=progress,
    )
