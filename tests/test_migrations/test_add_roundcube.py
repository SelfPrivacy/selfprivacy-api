# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

from selfprivacy_api.migrations.add_roundcube import AddRoundcube

from tests.test_migrations.conftest import (
    BASE_SERVICES,
    FLAKE_ALL_SERVICES,
    read_flake_services,
    sp_module_url,
)

FLAKE_WITHOUT_ROUNDCUBE = {
    name: sp_module_url(name) for name in BASE_SERVICES + ["monitoring"]
}


async def test_migrate_adds_roundcube_input(flake_file):
    flake_file(FLAKE_WITHOUT_ROUNDCUBE)
    migration = AddRoundcube()

    assert await migration.is_migration_needed() is True

    await migration.migrate()

    assert await read_flake_services() == {
        **FLAKE_WITHOUT_ROUNDCUBE,
        "roundcube": sp_module_url("roundcube"),
    }
    assert await migration.is_migration_needed() is False


async def test_not_needed_when_roundcube_present(flake_file):
    flake_file(FLAKE_ALL_SERVICES)

    assert await AddRoundcube().is_migration_needed() is False
    assert await read_flake_services() == FLAKE_ALL_SERVICES
