from selfprivacy_api.migrations.migration import Migration

from selfprivacy_api.utils import ReadUserData, WriteUserData


class AddRoundcubeToUserdata(Migration):
    """Add Roundcube to userdata.json if it does not exist"""

    def get_migration_name(self):
        return "add_roundcube_to_userdata"

    def get_migration_description(self):
        return "Add Roundcube to userdata.json if it does not exist"

    def is_migration_needed(self):
        with ReadUserData() as data:
            if "roundcube" not in data["modules"]:
                return True

    def migrate(self):
        with WriteUserData() as data:
            data["modules"]["roundcube"] = {
                "subdomain": "roundcube",
            }
