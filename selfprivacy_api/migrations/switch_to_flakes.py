import logging

from selfprivacy_api.migrations.migration import Migration

from selfprivacy_api.services.flake_service_manager import FlakeServiceManager
from selfprivacy_api.utils import ReadUserData, WriteUserData

logger = logging.getLogger(__name__)

class SwitchToFlakes(Migration):
    """Switch back to the stable branch from the SSO branch."""

    def get_migration_name(self) -> str:
        return "switch_to_flakes"

    def get_migration_description(self) -> str:
        return "Switch back to the stable branch from the SSO branch."

    def is_migration_needed(self) -> bool:
        with FlakeServiceManager() as manager:
            for service_url in manager.services.values():
                logger.info(
                    f"Checking if migration is needed for {service_url}"
                )
                if service_url.startswith(
                    "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=sso"
                ):
                    logger.info(
                        f"Migration is needed for {service_url}"
                    )
                    return True
                logger.info(f"Migration is not needed for {service_url}")
        return False

    def migrate(self) -> None:
        with FlakeServiceManager() as manager:
            # Go over each service, and if it has `ref=sso`, replace it with `ref=flakes`
            for key, value in manager.services.items():
                if value.startswith(
                    "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=sso"
                ):
                    logger.info(
                        f"Replacing {value} with {value.replace('ref=sso', 'ref=flakes')}"
                    )
                    manager.services[key] = value.replace("ref=sso", "ref=flakes")
