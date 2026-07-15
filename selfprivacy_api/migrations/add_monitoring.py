from selfprivacy_api.migrations.migration import Migration

from selfprivacy_api.services.flake_service_manager import (
    FlakeServiceManager,
    get_sp_module_url,
)
from selfprivacy_api.utils import ReadUserData, WriteUserData
from selfprivacy_api.utils.block_devices import BlockDevices


class AddMonitoring(Migration):
    """Adds monitoring service if it is not present."""

    def get_migration_name(self) -> str:
        return "add_monitoring"

    def get_migration_description(self) -> str:
        return "Adds the Monitoring if it is not present."

    async def is_migration_needed(self) -> bool:
        async with FlakeServiceManager() as manager:
            if "monitoring" not in manager.services:
                return True
        with ReadUserData() as data:
            if "monitoring" not in data["modules"]:
                return True
        return False

    async def migrate(self) -> None:
        async with FlakeServiceManager() as manager:
            if "monitoring" not in manager.services:
                manager.services["monitoring"] = get_sp_module_url(
                    manager.nixos_config, "monitoring"
                )
        with WriteUserData() as data:
            if "monitoring" not in data["modules"]:
                data["modules"]["monitoring"] = {
                    "enable": True,
                    "location": BlockDevices().get_root_block_device().canonical_name,
                }
