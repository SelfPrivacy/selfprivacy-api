import glob
import os
import re
import subprocess

from selfprivacy_api.migrations.migration import Migration
from selfprivacy_api.utils import ReadUserData, WriteUserData
from selfprivacy_api.utils.block_devices import BlockDevices


PARTITION_BY_ID_SUFFIX = re.compile(r"-part\d+$")
# one disk might expose multiple stable /dev/disk/by-id aliases. prefer globally
# unique hardware id first (wwn), fallback to bus-specific ids used by Hetzner after that.
BY_ID_PREFERENCE = ("wwn-", "scsi-", "ata-")
EFI_FIRMWARE_PATH = "/sys/firmware/efi"


def is_efi_booted() -> bool:
    return os.path.isdir(EFI_FIRMWARE_PATH)


def get_system_disk_by_id() -> str:
    """Return a stable whole-disk path for the disk containing /"""

    root_partition = BlockDevices().get_root_block_device().path
    parent_name = subprocess.check_output(
        ["lsblk", "-n", "-o", "PKNAME", root_partition], text=True
    ).strip()
    if not parent_name:
        raise RuntimeError(f"No parent disk found for root partition {root_partition}")

    disk = f"/dev/{parent_name}"
    resolved_disk = os.path.realpath(disk)
    candidates = sorted(
        path
        for path in glob.glob("/dev/disk/by-id/*")
        if not PARTITION_BY_ID_SUFFIX.search(path)
        and os.path.realpath(path) == resolved_disk
    )

    for prefix in BY_ID_PREFERENCE:
        for path in candidates:
            if os.path.basename(path).startswith(prefix):
                return path

    raise RuntimeError(
        f"No supported /dev/disk/by-id link found for system disk {disk}"
    )


class ConfigureHetznerBootloader(Migration):
    """Add the stable MBR GRUB installation target to userdata on Hetzner servers."""

    def get_migration_name(self) -> str:
        return "configure_hetzner_bootloader"

    def get_migration_description(self) -> str:
        return "Store the stable disk path used for grub mbr"

    async def is_migration_needed(self) -> bool:
        with ReadUserData() as data:
            provider = data.get("server", {}).get("provider")
            return (
                provider == "HETZNER"
                and not is_efi_booted()
                and "bootloader" not in data.get("server", {})
            )

    async def migrate(self) -> None:
        device = get_system_disk_by_id()
        with WriteUserData() as data:
            server = data.setdefault("server", {})
            server.setdefault(
                "bootloader",
                {
                    "type": "grub-mbr",
                    "device": device,
                },
            )
