from selfprivacy_api.migrations.migration import Migration

from selfprivacy_api.services.flake_service_manager import FlakeServiceManager
from selfprivacy_api.utils import ReadUserData, WriteUserData


class AddAuth(Migration):
    """Adds auth (kanidm) service if it is not present."""

    def get_migration_name(self) -> str:
        return "add_auth"

    def get_migration_description(self) -> str:
        return "Adds the auth (Kanidm) if it is not present."

    def is_migration_needed(self) -> bool:
        with FlakeServiceManager() as manager:
            if "auth" not in manager.services:
                return True
        with ReadUserData() as data:
            if "auth" not in data["modules"]:
                return True
        return False

    def migrate(self) -> None:
        with FlakeServiceManager() as manager:
            if "auth" not in manager.services:
                manager.services["monitoring"] = (
                    "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=sso&rev=f795bc977f03de64c10a62528bfa04a88f2611ca&dir=sp-modules/auth"
                )
        with WriteUserData() as data:
            if "monitoring" not in data["modules"]:
                data["modules"]["monitoring"] = {
                    "enable": False,
                }
