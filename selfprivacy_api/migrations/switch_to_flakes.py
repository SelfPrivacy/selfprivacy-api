from selfprivacy_api.migrations.migration import Migration

from selfprivacy_api.services.flake_service_manager import FlakeServiceManager
from selfprivacy_api.utils import ReadUserData, WriteUserData


class SwitchToFlakes(Migration):
    """Switch back to the stable branch from the SSO branch."""

    def get_migration_name(self) -> str:
        return "switch_to_flakes"

    def get_migration_description(self) -> str:
        return "Switch back to the stable branch from the SSO branch."

    def is_migration_needed(self) -> bool:
        with FlakeServiceManager() as manager:
            for service_url in manager.services.values():
                if service_url.startswith(
                    "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=sso"
                ):
                    return True
        return False

    def migrate(self) -> None:
        with FlakeServiceManager() as manager:
            # Go over each service, and if it has `ref=sso`, replace it with `ref=flakes`
            for key, value in manager.services.items():
                if value.startswith(
                    "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=sso"
                ):
                    manager.services[key] = value.replace("ref=sso", "ref=flakes")
