from selfprivacy_api.migrations.migration import Migration
from selfprivacy_api.services.flake_service_manager import FlakeServiceManager
from selfprivacy_api.utils.nix import evaluate_nix_file

import os


class MergeSpModulesFlake(Migration):
    """Merges sp-modules/flake.nix and nixos/flake.nix."""

    def get_migration_name(self) -> str:
        return "merge_sp_modules_flake"

    def get_migration_description(self) -> str:
        return "Merges sp-modules/flake.nix and nixos/flake.nix."

    async def is_migration_needed(self) -> bool:
        return os.path.isdir("/etc/nixos/sp-modules")

    async def migrate(self) -> None:
        current_services = await evaluate_nix_file(
            "/etc/nixos/sp-modules/flake.nix", "f: f.inputs"
        )

        os.rename("/etc/nixos/sp-modules", "/etc/nixos/.legacy-sp-modules")

        async with FlakeServiceManager() as manager:
            for key, value in current_services.items():
                manager.services[key] = value["url"]
