from selfprivacy_api.migrations.migration import Migration
from selfprivacy_api.utils import ReadUserData, WriteUserData


class CreateProviderFields(Migration):
    """Unhardcode providers"""

    def get_migration_name(self):
        return "create_provider_fields"

    def get_migration_description(self):
        return "Add DNS, backup and server provider fields to enable user to choose between different clouds and to make the deployment adapt to these preferences."

    def is_migration_needed(self):
        try:
            with ReadUserData() as userdata:
                return "dns" not in userdata
        except Exception as e:
            print(e)
            return False

    def migrate(self):
        # Write info about providers to userdata.json
        try:
            with WriteUserData() as userdata:
                userdata["dns"] = {
                    "provider": "CLOUDFLARE",
                    "apiToken": userdata["cloudflare"]["apiToken"],
                }
                userdata["server"] = {
                    "provider": "HETZNER",
                }
                userdata["backup"] = {
                    "provider": "BACKBLAZE",
                    "accountId": userdata["backblaze"]["accountId"],
                    "accountKey": userdata["backblaze"]["accountKey"],
                    "bucket": userdata["backblaze"]["bucket"],
                }

            print("Done")
        except Exception as e:
            print(e)
            print("Error migrating provider fields")
