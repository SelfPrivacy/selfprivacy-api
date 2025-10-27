from selfprivacy_api.migrations.migration import Migration

from selfprivacy_api.services.flake_service_manager import FlakeServiceManager


class AddRoundcube(Migration):
    """Adds the Roundcube if it is not present."""

    def get_migration_name(self) -> str:
        return "add_roundcube"

    def get_migration_description(self) -> str:
        return "Adds the Roundcube if it is not present."

    async def is_migration_needed(self) -> bool:
        with FlakeServiceManager() as manager:
            if "roundcube" not in manager.services:
                return True
        return False

    async def migrate(self) -> None:
        with FlakeServiceManager() as manager:
            if "roundcube" not in manager.services:
                manager.services["roundcube"] = (
                    "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/roundcube"
                )
