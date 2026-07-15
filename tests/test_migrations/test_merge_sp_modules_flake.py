import pytest

from selfprivacy_api.exceptions.system import ShellException
from selfprivacy_api.migrations.merge_sp_modules_flake import MergeSpModulesFlake
from selfprivacy_api.services.flake_service_manager import (
    SP_MODULE_INPUT_PREFIX,
    DEFAULT_NIXOS_CONFIG_URL,
    FlakeServiceManager,
    get_sp_module_url,
)
from selfprivacy_api.utils.nix import evaluate_nix_file
from tests.test_migrations.conftest import flake_content

LEGACY_SERVICES = {
    "nextcloud": get_sp_module_url(DEFAULT_NIXOS_CONFIG_URL, "nextcloud"),
    "roundcube": get_sp_module_url(DEFAULT_NIXOS_CONFIG_URL, "roundcube"),
}
TOP_LEVEL_INPUTS = {
    "selfprivacy-nixos-config": DEFAULT_NIXOS_CONFIG_URL,
    "sp-modules": "path:./sp-modules",
}


@pytest.fixture
def legacy_sp_modules_flake(mocker, tmp_path):
    """Create a legacy sp-modules flake and a top-level flake under tmp_path."""
    nixos_dir = tmp_path / "nixos"
    legacy_dir = nixos_dir / "sp-modules"
    legacy_dir.mkdir(parents=True)

    # old flake had just { <servicename>.url = <url>; }
    (legacy_dir / "flake.nix").write_text(flake_content({}, inputs=LEGACY_SERVICES))

    top_level_flake = nixos_dir / "flake.nix"
    top_level_flake.write_text(flake_content({}, inputs=TOP_LEVEL_INPUTS))

    mocker.patch(
        "selfprivacy_api.services.flake_service_manager.LEGACY_SP_MODULES_DIR",
        new=str(legacy_dir),
    )
    mocker.patch(
        "selfprivacy_api.migrations.merge_sp_modules_flake.LEGACY_SP_MODULES_BACKUP_DIR",
        new=str(nixos_dir / ".legacy-sp-modules"),
    )
    mocker.patch(
        "selfprivacy_api.services.flake_service_manager.FLAKE_CONFIG_PATH",
        new=str(top_level_flake),
    )
    return nixos_dir, legacy_dir, top_level_flake


async def test_not_needed_without_legacy_sp_modules(tmp_path, mocker):
    legacy_dir = tmp_path / "nixos" / "sp-modules"
    mocker.patch(
        "selfprivacy_api.services.flake_service_manager.LEGACY_SP_MODULES_DIR",
        new=str(legacy_dir),
    )

    assert await MergeSpModulesFlake().is_migration_needed() is False


async def test_migrate_merges_real_legacy_flake(legacy_sp_modules_flake):
    nixos_dir, legacy_dir, top_level_flake = legacy_sp_modules_flake
    migration = MergeSpModulesFlake()

    assert await migration.is_migration_needed() is True

    await migration.migrate()

    # The result is evaluated by real nix, rather than inferred from text.
    inputs = await evaluate_nix_file(top_level_flake, "f: f.inputs")
    assert inputs == {
        "selfprivacy-nixos-config": {"url": DEFAULT_NIXOS_CONFIG_URL},
        f"{SP_MODULE_INPUT_PREFIX}nextcloud": {"url": LEGACY_SERVICES["nextcloud"]},
        f"{SP_MODULE_INPUT_PREFIX}roundcube": {"url": LEGACY_SERVICES["roundcube"]},
    }

    async with FlakeServiceManager() as manager:
        assert manager.services == LEGACY_SERVICES
        assert manager.inputs == {
            "selfprivacy-nixos-config": {"url": DEFAULT_NIXOS_CONFIG_URL},
        }

    assert not legacy_dir.exists()
    assert (nixos_dir / ".legacy-sp-modules" / "flake.nix").is_file()
    assert await migration.is_migration_needed() is False


async def test_failed_merge_keeps_legacy_flake(legacy_sp_modules_flake, mocker):
    nixos_dir, legacy_dir, top_level_flake = legacy_sp_modules_flake
    original_top_level_flake = top_level_flake.read_text()

    async def fail_formatting(_):
        raise RuntimeError("failed to format flake")

    mocker.patch(
        "selfprivacy_api.services.flake_service_manager.format_nix_expr",
        side_effect=fail_formatting,
    )

    with pytest.raises(RuntimeError, match="failed to format flake"):
        await MergeSpModulesFlake().migrate()

    assert legacy_dir.is_dir()
    assert not (nixos_dir / ".legacy-sp-modules").exists()
    assert top_level_flake.read_text() == original_top_level_flake


async def test_invalid_legacy_flake_is_not_archived(legacy_sp_modules_flake):
    nixos_dir, legacy_dir, _ = legacy_sp_modules_flake
    (legacy_dir / "flake.nix").write_text("this is not valid Nix")

    with pytest.raises(ShellException):
        await MergeSpModulesFlake().migrate()

    assert legacy_dir.is_dir()
    assert not (nixos_dir / ".legacy-sp-modules").exists()
