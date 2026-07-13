# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

from selfprivacy_api.migrations.add_postgres_location import AddPostgresLocation
from selfprivacy_api.utils import ReadUserData, WriteUserData


async def test_needed_when_no_postgresql_section(generic_userdata):
    assert await AddPostgresLocation().is_migration_needed() is True


async def test_needed_when_location_missing(generic_userdata):
    with WriteUserData() as data:
        data["postgresql"] = {}

    assert await AddPostgresLocation().is_migration_needed() is True


async def test_not_needed_when_location_present(generic_userdata):
    with WriteUserData() as data:
        data["postgresql"] = {"location": "sdb"}

    assert await AddPostgresLocation().is_migration_needed() is False


async def test_migrate_uses_pleroma_location(generic_userdata):
    # No lsblk fake installed: with a pleroma location present,
    # BlockDevices must not be consulted.
    migration = AddPostgresLocation()

    await migration.migrate()

    with ReadUserData() as data:
        assert data["postgresql"] == {"location": "sdb"}
    assert await migration.is_migration_needed() is False


async def test_migrate_falls_back_to_root_device(block_devices):
    with WriteUserData() as data:
        del data["modules"]["pleroma"]
    migration = AddPostgresLocation()

    await migration.migrate()

    with ReadUserData() as data:
        assert data["postgresql"] == {"location": "sda1"}
    assert await migration.is_migration_needed() is False
