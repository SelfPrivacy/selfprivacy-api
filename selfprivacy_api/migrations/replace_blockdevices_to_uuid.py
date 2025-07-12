from typing import Optional
import logging
import subprocess

from selfprivacy_api.migrations.migration import Migration

from selfprivacy_api.utils import ReadUserData, WriteUserData
from selfprivacy_api.graphql.queries.system import get_system_provider_info

logger = logging.getLogger(__name__)

SYSTEM_BLOCK_DISK = "/dev/sda"
DIGITALOCEAN_EXTENDED_BLOCK_DISK = "/dev/vda1"
HETZNER_EXTENDED_BLOCK_DISK = "/dev/sdb"

EXTENDED_BLOCK_DISKS = [DIGITALOCEAN_EXTENDED_BLOCK_DISK, HETZNER_EXTENDED_BLOCK_DISK]


class ReplaceBlockDevicesToUUID(Migration):
    """Replace block devices to UUID"""

    def get_migration_name(self) -> str:
        return "replace_block_devices_to_uuid"

    def get_migration_description(self) -> str:
        return f"Replace {SYSTEM_BLOCK_DISK} and extended {EXTENDED_BLOCK_DISKS} with /dev/disk/by-uuid/<UUID>"

    def is_migration_needed(self) -> bool:
        with ReadUserData() as data:
            if "volumes" in data:
                if "device" in data["volumes"]:
                    if data["volumes"]["device"] == SYSTEM_BLOCK_DISK:
                        return True
        return False

    @staticmethod
    def _get_uuid(device: str) -> Optional[str]:
        """
        Run blkid and return the raw UUID string,
        or None on failure.
        """
        try:
            uuid = subprocess.check_output(
                ["blkid", "-s", "UUID", "-o", "value", device],
                text=True,
            )
            if not uuid:
                logger.error(
                    f"ReplaceBlockDevicesToUUID._get_uuid: failed to get UUID for {device}"
                )
            return uuid
        except subprocess.CalledProcessError as error:
            logger.warning(
                f"ReplaceBlockDevicesToUUID._get_uuid: failed to get UUID for {device}. {error}"
            )

    @staticmethod
    def _match_and_return_correct_uuid(
        disk: str,
        system_disk_uuid_path: str,
        extended_disk_uuid_path: str,
    ) -> Optional[str]:
        """
        Given a disk string (/dev/sda, /dev/vda1, /dev/sdb),
        return the matching UUID-path or None.
        """
        if disk == SYSTEM_BLOCK_DISK:
            return system_disk_uuid_path

        elif disk in EXTENDED_BLOCK_DISKS:
            return extended_disk_uuid_path

    def migrate(self) -> None:
        system_provider_info = get_system_provider_info()

        if system_provider_info.provider == "DIGITALOCEAN":
            extended_disk_uuid = ReplaceBlockDevicesToUUID._get_uuid(
                device=DIGITALOCEAN_EXTENDED_BLOCK_DISK
            )
        elif system_provider_info.provider == "HETZNER":
            extended_disk_uuid = ReplaceBlockDevicesToUUID._get_uuid(
                device=HETZNER_EXTENDED_BLOCK_DISK
            )
        else:
            logger.error(
                "Migration replace_block_devices_to_uuid failed: unknown provider"
            )
            return

        system_disk_uuid = ReplaceBlockDevicesToUUID._get_uuid(device=SYSTEM_BLOCK_DISK)

        if system_disk_uuid is None or extended_disk_uuid is None:
            logger.error(
                "Migration replace_block_devices_to_uuid failed: system_disk_uuid or extended_disk_uuid is None"
            )
            return

        system_disk_uuid_path = f"/dev/disk/by-uuid/{system_disk_uuid}"
        extended_disk_uuid_path = f"/dev/disk/by-uuid/{extended_disk_uuid}"

        with WriteUserData() as data:
            if "volumes" in data:
                if "device" in data["volumes"]:
                    data["volumes"]["device"] = system_disk_uuid_path

            if "modules" in data:
                for module in data["modules"]:
                    if "location" in module:
                        module["location"] = (
                            ReplaceBlockDevicesToUUID._match_and_return_correct_uuid(
                                disk=module["location"],
                                system_disk_uuid_path=system_disk_uuid_path,
                                extended_disk_uuid_path=extended_disk_uuid_path,
                            )
                        )

            if "postgresql" in data:
                data["postgresql"]["location"] = (
                    ReplaceBlockDevicesToUUID._match_and_return_correct_uuid(
                        disk=data["postgresql"]["location"],
                        system_disk_uuid_path=system_disk_uuid_path,
                        extended_disk_uuid_path=extended_disk_uuid_path,
                    )
                )

            data["bootDisk"] = system_disk_uuid_path
