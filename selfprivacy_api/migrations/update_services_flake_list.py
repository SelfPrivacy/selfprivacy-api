from selfprivacy_api.migrations.migration import Migration
from selfprivacy_api.jobs import JobStatus, Jobs

from selfprivacy_api.services.flake_service_manager import FlakeServiceManager


class UpdateServicesFlakeList(Migration):
    """Check if all required services are in the flake list"""

    def get_migration_name(self):
        return "update_services_flake_list"

    def get_migration_description(self):
        return "Check if all required services are in the flake list"

    def is_migration_needed(self):
        with FlakeServiceManager() as manager:
            if "roundcube" not in manager.services:
                return True

    def migrate(self):
        with FlakeServiceManager() as manager:
            if "roundcube" not in manager.services:
                manager.services[
                    "roundcube"
                ] = "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/roundcube"
