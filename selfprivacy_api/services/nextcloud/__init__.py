"""Class representing Nextcloud service."""
import base64
import subprocess
import time
import typing
import psutil
import pathlib
import shutil
from selfprivacy_api.jobs import Job, JobStatus, Jobs
from selfprivacy_api.services.service import Service, ServiceDnsRecord, ServiceStatus
from selfprivacy_api.utils import ReadUserData, WriteUserData
from selfprivacy_api.utils.block_devices import BlockDevice
from selfprivacy_api.utils.huey import huey

class Nextcloud(Service):
    """Class representing Nextcloud service."""

    def get_id(self) -> str:
        """Return service id."""
        return "nextcloud"

    def get_display_name(self) -> str:
        """Return service display name."""
        return "Nextcloud"

    def get_description(self) -> str:
        """Return service description."""
        return "Nextcloud is a cloud storage service that offers a web interface and a desktop client."

    def get_svg_icon(self) -> str:
        """Read SVG icon from file and return it as base64 encoded string."""
        with open("selfprivacy_api/services/nextcloud/nextcloud.svg", "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def is_enabled(self) -> bool:
        with ReadUserData() as user_data:
            return user_data.get("nextcloud", {}).get("enable", False)

    def get_status(self) -> ServiceStatus:
        """
        Return Nextcloud status from systemd.
        Use command return code to determine status.

        Return code 0 means service is running.
        Return code 1 or 2 means service is in error stat.
        Return code 3 means service is stopped.
        Return code 4 means service is off.
        """
        service_status = subprocess.Popen(
            ["systemctl", "status", "phpfpm-nextcloud.service"]
        )
        service_status.communicate()[0]
        if service_status.returncode == 0:
            return ServiceStatus.RUNNING
        elif service_status.returncode == 1 or service_status.returncode == 2:
            return ServiceStatus.ERROR
        elif service_status.returncode == 3:
            return ServiceStatus.STOPPED
        elif service_status.returncode == 4:
            return ServiceStatus.OFF
        else:
            return ServiceStatus.DEGRADED

    def enable(self):
        """Enable Nextcloud service."""
        with WriteUserData() as user_data:
            if "nextcloud" not in user_data:
                user_data["nextcloud"] = {}
            user_data["nextcloud"]["enable"] = True

    def disable(self):
        """Disable Nextcloud service."""
        with WriteUserData() as user_data:
            if "nextcloud" not in user_data:
                user_data["nextcloud"] = {}
            user_data["nextcloud"]["enable"] = False

    def stop(self):
        """Stop Nextcloud service."""
        subprocess.Popen(["systemctl", "stop", "phpfpm-nextcloud.service"])

    def start(self):
        """Start Nextcloud service."""
        subprocess.Popen(["systemctl", "start", "phpfpm-nextcloud.service"])

    def restart(self):
        """Restart Nextcloud service."""
        subprocess.Popen(["systemctl", "restart", "phpfpm-nextcloud.service"])

    def get_configuration(self) -> dict:
        """Return Nextcloud configuration."""
        return {}

    def set_configuration(self, config_items):
        return super().set_configuration(config_items)

    def get_logs(self):
        """Return Nextcloud logs."""
        return ""

    def get_storage_usage(self) -> int:
        """
        Calculate the real storage usage of /var/lib/nextcloud and all subdirectories.
        Calculate using pathlib.
        Do not follow symlinks.
        """
        storage_usage = 0
        for path in pathlib.Path("/var/lib/nextcloud").rglob("**/*"):
            if path.is_dir():
                continue
            storage_usage += path.stat().st_size
        return storage_usage

    def get_location(self) -> str:
        """Get the name of disk where Nextcloud is installed."""
        with ReadUserData() as user_data:
            if user_data.get("useBinds", False):
                return user_data.get("nextcloud", {}).get("location", "sda1")
            else:
                return "sda1"

    def get_dns_records(self) -> typing.List[ServiceDnsRecord]:
        return super().get_dns_records()

    def move_to_volume(self, volume: BlockDevice):
        job = Jobs().add(
            name="services.nextcloud.move",
            description=f"Moving Nextcloud to volume {volume.name}",
        )
        move_nextcloud(self, volume, job)
        return job


@huey.task()
def move_nextcloud(nextcloud: Nextcloud, volume: BlockDevice, job: Job):
    """Move Nextcloud to another volume."""
    job = Jobs().update(
        job=job,
        status_text="Performing pre-move checks...",
        status=JobStatus.RUNNING,
    )
    with ReadUserData() as user_data:
        if not user_data.get("useBinds", False):
            Jobs().update(
                job=job,
                status=JobStatus.ERROR,
                error="Server is not using binds.",
            )
            return
    # Check if we are on the same volume
    old_location = nextcloud.get_location()
    if old_location == volume.name:
        Jobs().update(
            job=job,
            status=JobStatus.ERROR,
            error="Nextcloud is already on this volume.",
        )
        return
    # Check if there is enough space on the new volume
    if volume.fsavail < nextcloud.get_storage_usage():
        Jobs().update(
            job=job,
            status=JobStatus.ERROR,
            error="Not enough space on the new volume.",
        )
        return
    # Make sure the volume is mounted
    if f"/volumes/{volume.name}" not in volume.mountpoints:
        Jobs().update(
            job=job,
            status=JobStatus.ERROR,
            error="Volume is not mounted.",
        )
        return
    # Make sure current actual directory exists
    if not pathlib.Path(f"/volumes/{old_location}/nextcloud").exists():
        Jobs().update(
            job=job,
            status=JobStatus.ERROR,
            error="Nextcloud is not found.",
        )
        return

    # Stop Nextcloud
    Jobs().update(
        job=job,
        status=JobStatus.RUNNING,
        status_text="Stopping Nextcloud...",
        progress=5,
    )
    nextcloud.stop()
    # Wait for Nextcloud to stop, check every second
    # If it does not stop in 30 seconds, abort
    for _ in range(30):
        if nextcloud.get_status() != ServiceStatus.RUNNING:
            break
        time.sleep(1)
    else:
        Jobs().update(
            job=job,
            status=JobStatus.ERROR,
            error="Nextcloud did not stop in 30 seconds.",
        )
        return

    # Unmount old volume
    Jobs().update(
        job=job,
        status_text="Unmounting old folder...",
        status=JobStatus.RUNNING,
        progress=10,
    )
    try:
        subprocess.run(["umount", "/var/lib/nextcloud"], check=True)
    except subprocess.CalledProcessError:
        Jobs().update(
            job=job,
            status=JobStatus.ERROR,
            error="Unable to unmount old volume.",
        )
        return
    # Move data to new volume and set correct permissions
    Jobs().update(
        job=job,
        status_text="Moving data to new volume...",
        status=JobStatus.RUNNING,
        progress=20,
    )
    shutil.move(
        f"/volumes/{old_location}/nextcloud", f"/volumes/{volume.name}/nextcloud"
    )

    Jobs().update(
        job=job,
        status_text="Making sure Nextcloud owns its files...",
        status=JobStatus.RUNNING,
        progress=70,
    )
    try:
        subprocess.run(
            [
                "chown",
                "-R",
                "nextcloud:nextcloud",
                f"/volumes/{volume.name}/nextcloud",
            ],
            check=True,
        )
    except subprocess.CalledProcessError as error:
        print(error.output)
        Jobs().update(
            job=job,
            status=JobStatus.RUNNING,
            error="Unable to set ownership of new volume. Nextcloud may not be able to access its files. Continuing anyway.",
        )
        return

    # Mount new volume
    Jobs().update(
        job=job,
        status_text="Mounting Nextcloud data...",
        status=JobStatus.RUNNING,
        progress=90,
    )
    try:
        subprocess.run(
            [
                "mount",
                "--bind",
                f"/volumes/{volume.name}/nextcloud",
                "/var/lib/nextcloud",
            ],
            check=True,
        )
    except subprocess.CalledProcessError as error:
        print(error.output)
        Jobs().update(
            job=job,
            status=JobStatus.ERROR,
            error="Unable to mount new volume.",
        )
        return

    # Update userdata
    Jobs().update(
        job=job,
        status_text="Finishing move...",
        status=JobStatus.RUNNING,
        progress=95,
    )
    with WriteUserData() as user_data:
        if "nextcloud" not in user_data:
            user_data["nextcloud"] = {}
        user_data["nextcloud"]["location"] = volume.name
    # Start Nextcloud
    nextcloud.start()
    Jobs().update(
        job=job,
        status=JobStatus.FINISHED,
        result="Nextcloud moved successfully.",
        status_text="Starting Nextcloud...",
        progress=100,
    )
