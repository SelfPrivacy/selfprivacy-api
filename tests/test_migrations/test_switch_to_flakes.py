# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

from selfprivacy_api.migrations.switch_to_flakes import SwitchToFlakes

from tests.test_migrations.conftest import (
    FLAKE_ALL_SERVICES,
    FLAKE_WITH_SSO_REFS,
    THIRD_PARTY_SSO_URL,
    read_flake_services,
    sp_module_url,
)


async def test_migrate_rewrites_sso_refs_to_flakes(flake_file):
    flake_file(FLAKE_WITH_SSO_REFS)
    migration = SwitchToFlakes()

    assert await migration.is_migration_needed() is True

    await migration.migrate()

    assert await read_flake_services() == {
        # dir= suffix stays intact, only the ref changes
        "bitwarden": sp_module_url("bitwarden"),
        "gitea": sp_module_url("gitea"),
        # already on flakes: unchanged
        "nextcloud": sp_module_url("nextcloud"),
        # contains "ref=sso" but is not a selfprivacy-nixos-config URL:
        # must not be rewritten
        "some-module": THIRD_PARTY_SSO_URL,
    }
    assert await migration.is_migration_needed() is False


async def test_not_needed_without_sso_refs(flake_file):
    flake_file(FLAKE_ALL_SERVICES)

    assert await SwitchToFlakes().is_migration_needed() is False
    assert await read_flake_services() == FLAKE_ALL_SERVICES
