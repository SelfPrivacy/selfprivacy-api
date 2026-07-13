# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

import json

import pytest

from selfprivacy_api.migrations import migrations as real_migrations
from selfprivacy_api.migrations import run_migrations
from selfprivacy_api.migrations.migration import Migration
from selfprivacy_api.repositories.tokens.redis_tokens_repository import (
    RedisTokensRepository,
)
from selfprivacy_api.utils import ReadUserData, UserDataFiles, WriteUserData

from tests.conftest import TOKENS
from tests.test_migrations.conftest import (
    ALL_USERS,
    FLAKE_ALL_SERVICES,
    ROOT_UUID,
    read_flake_services,
    set_api_secret,
)
from tests.test_migrations.test_migrate_users_from_json import kanidm_person


class RecordingMigration(Migration):
    def __init__(self, name: str, needed: bool = True, raise_in: str = ""):
        self.name = name
        self.needed = needed
        self.raise_in = raise_in
        self.calls: list[str] = []

    def get_migration_name(self) -> str:
        return self.name

    def get_migration_description(self) -> str:
        return f"Recording stub {self.name}"

    async def is_migration_needed(self) -> bool:
        self.calls.append("is_migration_needed")
        if self.raise_in == "is_migration_needed":
            raise RuntimeError(f"boom in {self.name}.is_migration_needed")
        return self.needed

    async def migrate(self) -> None:
        self.calls.append("migrate")
        if self.raise_in == "migrate":
            raise RuntimeError(f"boom in {self.name}.migrate")


def install_stubs(mocker, *stubs: RecordingMigration):
    # run_migrations reads the module global at call time
    mocker.patch("selfprivacy_api.migrations.migrations", new=list(stubs))


async def test_runs_needed_migrations_in_order(generic_userdata, mocker):
    first, second = RecordingMigration("a"), RecordingMigration("b")
    install_stubs(mocker, first, second)

    await run_migrations()

    assert first.calls == ["is_migration_needed", "migrate"]
    assert second.calls == ["is_migration_needed", "migrate"]


async def test_skips_migrate_when_not_needed(generic_userdata, mocker):
    stub = RecordingMigration("a", needed=False)
    install_stubs(mocker, stub)

    await run_migrations()

    assert stub.calls == ["is_migration_needed"]


async def test_skip_by_name(generic_userdata, mocker):
    skipped, running = RecordingMigration("a"), RecordingMigration("b")
    install_stubs(mocker, skipped, running)
    set_api_secret("skippedMigrations", ["a"])

    await run_migrations()

    assert skipped.calls == []
    assert running.calls == ["is_migration_needed", "migrate"]


async def test_disable_all(generic_userdata, mocker):
    first, second = RecordingMigration("a"), RecordingMigration("b")
    install_stubs(mocker, first, second)
    set_api_secret("skippedMigrations", ["DISABLE_ALL", "b"])

    await run_migrations()

    assert first.calls == []
    assert second.calls == []


@pytest.mark.parametrize("secrets_content", [{}, {"api": {}}])
async def test_runs_when_no_skip_configuration(
    generic_userdata, mocker, secrets_content
):
    stub = RecordingMigration("a")
    install_stubs(mocker, stub)
    with WriteUserData(UserDataFiles.SECRETS) as secrets:
        secrets.clear()
        secrets.update(secrets_content)

    await run_migrations()

    assert stub.calls == ["is_migration_needed", "migrate"]


@pytest.mark.parametrize("raise_in", ["is_migration_needed", "migrate"])
async def test_exception_does_not_block_next_migration(
    generic_userdata, mocker, raise_in
):
    failing = RecordingMigration("a", raise_in=raise_in)
    running = RecordingMigration("b")
    install_stubs(mocker, failing, running)

    await run_migrations()  # must not raise

    assert running.calls == ["is_migration_needed", "migrate"]


def test_real_migration_names_are_stable():
    # The skip mechanism is a user-facing contract keyed by these names.
    names = [migration.get_migration_name() for migration in real_migrations]
    assert names == [
        "write_token_to_redis",
        "check_for_system_rebuild_jobs",
        "merge_sp_modules_flake",
        "migrate_users_from_json",
        "add_postgres_location",
        "switch_to_flakes",
        "replace_block_devices_to_uuid",
        "add_monitoring",
    ]
    assert len(set(names)) == len(names)


async def test_run_migrations_noop_on_fully_migrated_system(
    generic_userdata,
    flake_file,
    redis_repo_with_tokens,
    jobs,
    kanidm_api,
    mock_kanidm_domain,
    mock_admin_token,
    mocker,
    tmp_path,
):
    """Startup on an up-to-date server must not touch anything: the real
    migration list runs against real fully-migrated state, with only the
    read-only Kanidm GET scripted at the boundary."""
    flake_file(FLAKE_ALL_SERVICES)
    mocker.patch(
        "selfprivacy_api.migrations.merge_sp_modules_flake.LEGACY_SP_MODULES_DIR",
        new=str(tmp_path / "absent-sp-modules"),
    )
    with WriteUserData() as data:
        data["postgresql"] = {"location": "sdb"}
        data["server"]["rootPartition"] = f"/dev/disk/by-uuid/{ROOT_UUID}"
    kanidm_api.respond(200, [kanidm_person(name) for name in ALL_USERS])
    check_output = mocker.patch("subprocess.check_output")

    with ReadUserData() as data:
        userdata_snapshot = json.loads(json.dumps(data))

    await run_migrations()

    assert len(kanidm_api.requests) == 1
    assert kanidm_api.requests[0].method == "GET"

    assert sorted(
        await RedisTokensRepository().get_tokens(), key=lambda token: token.token
    ) == sorted(TOKENS, key=lambda token: token.token)
    assert await read_flake_services() == FLAKE_ALL_SERVICES
    with ReadUserData() as data:
        assert data == userdata_snapshot
    assert jobs.get_jobs() == []
    # lsblk was never consulted
    assert check_output.call_count == 0
