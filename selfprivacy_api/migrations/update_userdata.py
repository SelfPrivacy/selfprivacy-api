from selfprivacy_api.migrations.migration import Migration

from selfprivacy_api.utils import ReadUserData, WriteUserData


class UpdateServicesFlakeList(Migration):
    """Check if all required services are in the flake list"""

    def get_migration_name(self):
        return "update_services_flake_list"

    def get_migration_description(self):
        return "Check if all required services are in the flake list"

    def is_migration_needed(self):
        with ReadUserData() as data:
            if "roundcube" not in data["modules"]:
                return True

    def migrate(self):
        with WriteUserData() as data:
            data["modules"]["roundcube"] = {
                "enable": True,
                "subdomain": "roundcube",
            }
