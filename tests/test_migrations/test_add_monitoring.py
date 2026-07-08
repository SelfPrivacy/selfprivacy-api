# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

from selfprivacy_api.migrations.add_monitoring import AddMonitoring
from selfprivacy_api.utils import ReadUserData, WriteUserData

from tests.test_migrations.conftest import (
    FLAKE_ALL_SERVICES,
    FLAKE_WITHOUT_MONITORING,
    read_flake_services,
    sp_module_url,
)


def remove_monitoring_module():
    with WriteUserData() as data:
        del data["modules"]["monitoring"]


async def test_needed_when_flake_lacks_monitoring(generic_userdata, flake_file):
    flake_file(FLAKE_WITHOUT_MONITORING)

    assert await AddMonitoring().is_migration_needed() is True


async def test_needed_when_userdata_lacks_monitoring(generic_userdata, flake_file):
    flake_file(FLAKE_ALL_SERVICES)
    remove_monitoring_module()

    assert await AddMonitoring().is_migration_needed() is True


async def test_not_needed_when_both_present(generic_userdata, flake_file):
    flake_file(FLAKE_ALL_SERVICES)

    assert await AddMonitoring().is_migration_needed() is False


async def test_migrate_adds_flake_input_and_module(flake_file, block_devices):
    # block_devices provides generic_userdata and the lsblk fake:
    # the root device location comes from real BlockDevices parsing.
    flake_file(FLAKE_WITHOUT_MONITORING)
    remove_monitoring_module()
    migration = AddMonitoring()

    assert await migration.is_migration_needed() is True

    await migration.migrate()

    assert await read_flake_services() == {
        **FLAKE_WITHOUT_MONITORING,
        "monitoring": sp_module_url("monitoring"),
    }
    with ReadUserData() as data:
        assert data["modules"]["monitoring"] == {
            "enable": True,
            "location": "sda1",
        }
    assert await migration.is_migration_needed() is False


async def test_migrate_preserves_existing_module_config(generic_userdata, flake_file):
    # No lsblk fake installed: the existing-module branch must not need it.
    flake_file(FLAKE_WITHOUT_MONITORING)
    migration = AddMonitoring()

    await migration.migrate()

    assert await read_flake_services() == {
        **FLAKE_WITHOUT_MONITORING,
        "monitoring": sp_module_url("monitoring"),
    }
    with ReadUserData() as data:
        # Untouched config from turned_on.json
        assert data["modules"]["monitoring"] == {
            "enable": True,
            "location": "sdb",
        }
    assert await migration.is_migration_needed() is False
