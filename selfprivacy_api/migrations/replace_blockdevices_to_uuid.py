from typing import Optional
import logging
import subprocess

from selfprivacy_api.migrations.migration import Migration

from selfprivacy_api.utils import ReadUserData, WriteUserData

logger = logging.getLogger(__name__)


class ReplaceBlockDevicesToUUID(Migration):
    """Replace block devices to UUID"""

    def get_migration_name(self) -> str:
        return "replace_block_devices_to_uuid"

    def get_migration_description(self) -> str:
        return "Replace /dev/sda and /dev/vda1 with /dev/disk/by-uuid/<UUID>"

    def is_migration_needed(self) -> bool:
        with ReadUserData() as data:
            if "volumes" in data:
                if "device" in data["volumes"]:
                    if data["volumes"]["device"] == "/dev/sda":
                        return True
        return False

    def migrate(self) -> None:
        def _get_uuid(device: str) -> Optional[str]:
            try:
                return subprocess.check_output(
                    ["blkid", "-s", "UUID", "-o", "value", device],
                    text=True,
                )
            except subprocess.CalledProcessError:
                logger.warning(f"Failed to get {device} uuid")
                return None

        sda_uuid = _get_uuid(device="/dev/sda")
        vda1_uuid = _get_uuid(device="/dev/vda1")

        if sda_uuid is None or vda1_uuid is None:
            return

        sda_path = f"/dev/disk/by-uuid/{sda_uuid}"
        vda1_path = f"/dev/disk/by-uuid/{vda1_uuid}"

        with WriteUserData() as data:
            if "volumes" in data:
                data["volumes"]["device"] = sda_path

            if "modules" in data:
                for module in data["volumes"]["modules"]:
                    if "location" in module:
                        if module["location"] == "sda":
                            module["location"] = sda_path

                        elif module["location"] == "vda1":
                            module["location"] = vda1_path

            if "postgresql" in data:
                if data["postgresql"]["location"] == "sda":
                    data["postgresql"]["location"] = sda_path

                elif data["postgresql"]["location"] == "vda1":
                    data["postgresql"]["location"] = vda1_path
