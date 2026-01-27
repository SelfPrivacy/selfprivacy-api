import subprocess

from selfprivacy_api.migrations.migration import Migration
from selfprivacy_api.utils.block_devices import BlockDevices


class EnableExt4EncryptionFeature(Migration):
    """Enables fscrypt support on ext4 filesystems"""

    def get_migration_name(self) -> str:
        return "enable_ext4_encryption_feature"

    def get_migration_description(self) -> str:
        return "Enables fscrypt support on ext4 filesystems"

    async def is_migration_needed(self) -> bool:
        return True

    async def migrate(self) -> None:
        devices = BlockDevices().lsblk_devices()

        for device in devices:
            if device.is_usable_partition() and device.fstype == "ext4":
                subprocess.check_output(["tune2fs", "-O", "encrypt", device.path])
