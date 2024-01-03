from selfprivacy_api.migrations.migration import Migration
from selfprivacy_api.utils import ReadUserData, WriteUserData
from selfprivacy_api.services import get_all_services


def migrate_services_to_modules():
    with WriteUserData() as userdata:
        if "modules" not in userdata.keys():
            userdata["modules"] = {}

        for service in get_all_services():
            name = service.get_id()
            if name in userdata.keys():
                field_content = userdata[name]
                userdata["modules"][name] = field_content
                del userdata[name]


# If you ever want to get rid of modules field you will need to get rid of this migration
class CreateModulesField(Migration):
    """introduce 'modules' (services) into userdata"""

    def get_migration_name(self):
        return "modules_in_json"

    def get_migration_description(self):
        return "Group service settings into a 'modules' field in userdata.json"

    def is_migration_needed(self) -> bool:
        try:
            with ReadUserData() as userdata:
                for service in get_all_services():
                    if service.get_id() in userdata.keys():
                        return True

                if "modules" not in userdata.keys():
                    return True
                return False
        except Exception as e:
            print(e)
            return False

    def migrate(self):
        # Write info about providers to userdata.json
        try:
            migrate_services_to_modules()
            print("Done")
        except Exception as e:
            print(e)
            print("Error migrating service fields")
