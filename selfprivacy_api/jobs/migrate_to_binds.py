"""Function to perform migration of app data to binds."""

import gettext
import subprocess
import asyncio
import pathlib
import shutil
import logging

from pydantic import BaseModel

from selfprivacy_api.jobs import Job, JobStatus, Jobs
from selfprivacy_api.services import ServiceManager
from selfprivacy_api.services.mailserver import MailServer
from selfprivacy_api.utils import ReadUserData, WriteUserData
from selfprivacy_api.utils.huey import huey, huey_async_helper
from selfprivacy_api.utils.block_devices import BlockDevices

logger = logging.getLogger(__name__)

_ = gettext.gettext


class BindMigrationConfig(BaseModel):
    """Config for bind migration.
    For each service provide block device name.
    """

    email_block_device: str
    bitwarden_block_device: str
    gitea_block_device: str
    nextcloud_block_device: str
    pleroma_block_device: str


def is_bind_migrated() -> bool:
    """Check if bind migration was performed."""
    with ReadUserData() as user_data:
        return user_data.get("useBinds", False)


def activate_binds(config: BindMigrationConfig):
    """Activate binds."""
    # Activate binds in userdata
    with WriteUserData() as user_data:
        if "email" not in user_data:
            user_data["email"] = {}
        user_data["email"]["location"] = config.email_block_device
        if "bitwarden" not in user_data:
            user_data["bitwarden"] = {}
        user_data["bitwarden"]["location"] = config.bitwarden_block_device
        if "gitea" not in user_data:
            user_data["gitea"] = {}
        user_data["gitea"]["location"] = config.gitea_block_device
        if "nextcloud" not in user_data:
            user_data["nextcloud"] = {}
        user_data["nextcloud"]["location"] = config.nextcloud_block_device
        if "pleroma" not in user_data:
            user_data["pleroma"] = {}
        user_data["pleroma"]["location"] = config.pleroma_block_device

        user_data["useBinds"] = True


def move_folder(
    data_path: pathlib.Path, bind_path: pathlib.Path, user: str, group: str
):
    """Move folder from data to bind."""
    if data_path.exists():
        shutil.move(str(data_path), str(bind_path))
    else:
        return

    try:
        data_path.mkdir(mode=0o750, parents=True, exist_ok=True)
    except Exception as error:
        logging.error(f"Error creating data path: {error}")
        return

    try:
        shutil.chown(str(bind_path), user=user, group=group)
        shutil.chown(str(data_path), user=user, group=group)
    except LookupError:
        pass

    try:
        subprocess.run(["mount", "--bind", str(bind_path), str(data_path)], check=True)
    except subprocess.CalledProcessError as error:
        logging.error(error)

    try:
        subprocess.run(["chown", "-R", f"{user}:{group}", str(data_path)], check=True)
    except subprocess.CalledProcessError as error:
        logging.error(error)


@huey.task()
def migrate_to_binds(config: BindMigrationConfig, job: Job):
    """Migrate app data to binds."""

    # Exit if migration is already done
    if is_bind_migrated():
        Jobs.update(
            job=job,
            status=JobStatus.ERROR,
            error=_("Migration already done."),
        )
        return

    Jobs.update(
        job=job,
        status=JobStatus.RUNNING,
        progress=0,
        status_text=_("Checking if services are present."),
    )

    nextcloud_service = huey_async_helper.run_async(
        ServiceManager.get_service_by_id("nextcloud")
    )
    bitwarden_service = huey_async_helper.run_async(
        ServiceManager.get_service_by_id("bitwarden")
    )
    gitea_service = huey_async_helper.run_async(
        ServiceManager.get_service_by_id("gitea")
    )
    pleroma_service = huey_async_helper.run_async(
        ServiceManager.get_service_by_id("pleroma")
    )

    if not nextcloud_service:
        Jobs.update(
            job=job,
            status=JobStatus.ERROR,
            error=_("Nextcloud service not found."),
        )
        return

    if not bitwarden_service:
        Jobs.update(
            job=job,
            status=JobStatus.ERROR,
            error=_("Bitwarden service not found."),
        )
        return

    if not gitea_service:
        Jobs.update(
            job=job,
            status=JobStatus.ERROR,
            error=_("Gitea service not found."),
        )
        return

    if not pleroma_service:
        Jobs.update(
            job=job,
            status=JobStatus.ERROR,
            error=_("Pleroma service not found."),
        )
        return

    Jobs.update(
        job=job,
        status=JobStatus.RUNNING,
        progress=0,
        status_text=_("Checking if all volumes are available."),
    )
    # Get block devices.
    block_devices = BlockDevices().get_block_devices()
    block_device_names = [device.canonical_name for device in block_devices]

    # Get all unique required block devices
    required_block_devices = []
    for block_device_name in config.__dict__.values():
        if block_device_name not in required_block_devices:
            required_block_devices.append(block_device_name)

    # Check if all block devices from config are present.
    for block_device_name in required_block_devices:
        if block_device_name not in block_device_names:
            Jobs.update(
                job=job,
                status=JobStatus.ERROR,
                error=_("Block device %(block_device_name)s not found.")
                % {"block_device_name": block_device_name},
            )
            return

    # Make sure all required block devices are mounted.
    # sda1 is the root partition and is always mounted.
    for block_device_name in required_block_devices:
        if block_device_name == "sda1":
            continue
        block_device = BlockDevices().get_block_device_by_canonical_name(
            block_device_name
        )
        if block_device is None:
            Jobs.update(
                job=job,
                status=JobStatus.ERROR,
                error=_("Block device %(block_device_name)s not found.")
                % {"block_device_name": block_device_name},
            )
            return
        if f"/volumes/{block_device_name}" not in block_device.mountpoints:
            Jobs.update(
                job=job,
                status=JobStatus.ERROR,
                error=_("Block device %(block_device_name)s not mounted.")
                % {"block_device_name": block_device_name},
            )
            return

    # Make sure /volumes/sda1 exists.
    pathlib.Path("/volumes/sda1").mkdir(parents=True, exist_ok=True)

    Jobs.update(
        job=job,
        status=JobStatus.RUNNING,
        progress=5,
        status_text=_("Activating binds in NixOS config."),
    )

    activate_binds(config)

    # Perform migration of Nextcloud.
    Jobs.update(
        job=job,
        status=JobStatus.RUNNING,
        progress=10,
        status_text=_("Migrating Nextcloud."),
    )

    huey_async_helper.run_async(nextcloud_service.stop())

    # If /volumes/sda1/nextcloud or /volumes/sdb/nextcloud exists, skip it.
    if not pathlib.Path("/volumes/sda1/nextcloud").exists():
        if not pathlib.Path("/volumes/sdb/nextcloud").exists():
            move_folder(
                data_path=pathlib.Path("/var/lib/nextcloud"),
                bind_path=pathlib.Path(
                    f"/volumes/{config.nextcloud_block_device}/nextcloud"
                ),
                user="nextcloud",
                group="nextcloud",
            )

    # Start Nextcloud
    huey_async_helper.run_async(nextcloud_service.start())

    # Perform migration of Bitwarden

    Jobs.update(
        job=job,
        status=JobStatus.RUNNING,
        progress=28,
        status_text=_("Migrating Bitwarden."),
    )

    huey_async_helper.run_async(bitwarden_service.stop())

    if not pathlib.Path("/volumes/sda1/bitwarden").exists():
        if not pathlib.Path("/volumes/sdb/bitwarden").exists():
            move_folder(
                data_path=pathlib.Path("/var/lib/bitwarden"),
                bind_path=pathlib.Path(
                    f"/volumes/{config.bitwarden_block_device}/bitwarden"
                ),
                user="vaultwarden",
                group="vaultwarden",
            )

    if not pathlib.Path("/volumes/sda1/bitwarden_rs").exists():
        if not pathlib.Path("/volumes/sdb/bitwarden_rs").exists():
            move_folder(
                data_path=pathlib.Path("/var/lib/bitwarden_rs"),
                bind_path=pathlib.Path(
                    f"/volumes/{config.bitwarden_block_device}/bitwarden_rs"
                ),
                user="vaultwarden",
                group="vaultwarden",
            )

    # Start Bitwarden
    huey_async_helper.run_async(bitwarden_service.start())

    # Perform migration of Gitea

    Jobs.update(
        job=job,
        status=JobStatus.RUNNING,
        progress=46,
        status_text=_("Migrating Gitea."),
    )

    huey_async_helper.run_async(gitea_service.stop())

    if not pathlib.Path("/volumes/sda1/gitea").exists():
        if not pathlib.Path("/volumes/sdb/gitea").exists():
            move_folder(
                data_path=pathlib.Path("/var/lib/gitea"),
                bind_path=pathlib.Path(f"/volumes/{config.gitea_block_device}/gitea"),
                user="gitea",
                group="gitea",
            )

    huey_async_helper.run_async(gitea_service.start())

    # Perform migration of Mail server

    Jobs.update(
        job=job,
        status=JobStatus.RUNNING,
        progress=64,
        status_text=_("Migrating Mail server."),
    )

    huey_async_helper.run_async(MailServer().stop())

    if not pathlib.Path("/volumes/sda1/vmail").exists():
        if not pathlib.Path("/volumes/sdb/vmail").exists():
            move_folder(
                data_path=pathlib.Path("/var/vmail"),
                bind_path=pathlib.Path(f"/volumes/{config.email_block_device}/vmail"),
                user="virtualMail",
                group="virtualMail",
            )

    if not pathlib.Path("/volumes/sda1/sieve").exists():
        if not pathlib.Path("/volumes/sdb/sieve").exists():
            move_folder(
                data_path=pathlib.Path("/var/sieve"),
                bind_path=pathlib.Path(f"/volumes/{config.email_block_device}/sieve"),
                user="virtualMail",
                group="virtualMail",
            )

    huey_async_helper.run_async(MailServer().start())

    # Perform migration of Pleroma

    Jobs.update(
        job=job,
        status=JobStatus.RUNNING,
        progress=82,
        status_text=_("Migrating Pleroma."),
    )

    huey_async_helper.run_async(pleroma_service.stop())

    if not pathlib.Path("/volumes/sda1/pleroma").exists():
        if not pathlib.Path("/volumes/sdb/pleroma").exists():
            move_folder(
                data_path=pathlib.Path("/var/lib/pleroma"),
                bind_path=pathlib.Path(
                    f"/volumes/{config.pleroma_block_device}/pleroma"
                ),
                user="pleroma",
                group="pleroma",
            )

    if not pathlib.Path("/volumes/sda1/postgresql").exists():
        if not pathlib.Path("/volumes/sdb/postgresql").exists():
            move_folder(
                data_path=pathlib.Path("/var/lib/postgresql"),
                bind_path=pathlib.Path(
                    f"/volumes/{config.pleroma_block_device}/postgresql"
                ),
                user="postgres",
                group="postgres",
            )

    huey_async_helper.run_async(pleroma_service.start())

    Jobs.update(
        job=job,
        status=JobStatus.FINISHED,
        progress=100,
        status_text=_("Migration finished."),
        result=_("Migration finished."),
    )


def start_bind_migration(config: BindMigrationConfig) -> Job:
    """Start migration."""
    job = Jobs.add(
        type_id="migrations.migrate_to_binds",
        name=_("Migrate to binds"),
        description=_("Migration required to use the new disk space management."),
    )
    migrate_to_binds(config, job)
    return job
