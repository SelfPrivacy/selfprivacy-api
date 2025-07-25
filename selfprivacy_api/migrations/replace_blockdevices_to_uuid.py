import logging

from selfprivacy_api.migrations.migration import Migration

from selfprivacy_api.utils import ReadUserData, WriteUserData
from selfprivacy_api.utils.block_devices import BlockDevices

logger = logging.getLogger(__name__)


class ReplaceBlockDevicesToUUID(Migration):
    """Replace block devices to UUID"""

    def get_migration_name(self) -> str:
        return "replace_block_devices_to_uuid"

    def get_migration_description(self) -> str:
        return "Replace volume block devices with UUIDs in user data"

    def is_migration_needed(self) -> bool:
        with ReadUserData() as data:
            if "server" in data:
                if "rootPartition" not in data["server"]:
                    return True
        return False

    def migrate(self) -> None:
        partitions = BlockDevices().get_block_devices()

        with WriteUserData() as user_data:
            if "server" not in user_data:
                user_data["server"] = {}

            for partition in partitions:
                if partition.is_root:
                    user_data["server"][
                        "rootPartition"
                    ] = f"/dev/disk/by-uuid/{partition.uuid}"
                    logger.info(
                        f"Set system partition to {partition.canonical_name} ({partition.uuid})"
                    )
                    user_data["server"]["rootPartitionName"] = partition.canonical_name
                    logger.info(
                        f"Set system partition name to {partition.canonical_name}"
                    )
                else:
                    for volume in user_data.get("volumes", []):
                        if volume["device"] == partition.path:
                            volume["device"] = f"/dev/disk/by-uuid/{partition.uuid}"
                            logger.info(
                                f"Replaced {partition.canonical_name} ({partition.uuid}) in volumes"
                            )
