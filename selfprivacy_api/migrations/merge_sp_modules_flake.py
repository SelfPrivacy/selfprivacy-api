from selfprivacy_api.migrations.migration import Migration
from selfprivacy_api.services.flake_service_manager import FlakeServiceManager
from selfprivacy_api.utils.nix import evaluate_nix_file

import os


LEGACY_SP_MODULES_DIR = "/etc/nixos/sp-modules"
LEGACY_SP_MODULES_BACKUP_DIR = "/etc/nixos/.legacy-sp-modules"


class MergeSpModulesFlake(Migration):
    """Merges sp-modules/flake.nix and nixos/flake.nix."""

    def get_migration_name(self) -> str:
        return "merge_sp_modules_flake"

    def get_migration_description(self) -> str:
        return "Merges sp-modules/flake.nix and nixos/flake.nix."

    async def is_migration_needed(self) -> bool:
        return os.path.isdir(LEGACY_SP_MODULES_DIR)

    async def migrate(self) -> None:
        current_services = await evaluate_nix_file(
            os.path.join(LEGACY_SP_MODULES_DIR, "flake.nix"), "f: f.inputs"
        )

        async with FlakeServiceManager() as manager:
            manager.inputs.pop("sp-modules", None)
            for key, value in current_services.items():
                manager.services[key] = value["url"]

        os.rename(LEGACY_SP_MODULES_DIR, LEGACY_SP_MODULES_BACKUP_DIR)
