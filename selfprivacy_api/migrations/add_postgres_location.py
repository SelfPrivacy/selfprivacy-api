from selfprivacy_api.migrations.migration import Migration
from selfprivacy_api.utils import WriteUserData, ReadUserData
from selfprivacy_api.utils.block_devices import BlockDevices


class AddPostgresLocation(Migration):
    """Add a location for Postgres, so it doesn't depend on Pleroma module"""

    def get_migration_name(self) -> str:
        return "add_postgres_location"

    def get_migration_description(self) -> str:
        return "Add a location for Postgres, so it doesn't depend on Pleroma module"

    def is_migration_needed(self) -> bool:
        with ReadUserData() as data:
            if "postgresql" not in data:
                return True
            if "location" not in data.get("postgresql", {}):
                return True
            return False

    def migrate(self) -> None:
        # Try to get Pleroma location
        with ReadUserData() as data:
            pleroma_location = (
                data.get("modules", {}).get("pleroma", {}).get("location", None)
            )

        if pleroma_location is None:
            pleroma_location = BlockDevices().get_root_block_device().name

        if pleroma_location is None:
            raise Exception("Couldn't get location for Postgres")

        with WriteUserData() as data:
            if "postgresql" not in data:
                data["postgresql"] = {}
            data["postgresql"]["location"] = pleroma_location
