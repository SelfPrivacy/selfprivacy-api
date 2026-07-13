"""Fixtures and helpers for tests of selfprivacy_api.migrations.

Philosophy: only true external boundaries are faked (Kanidm HTTP, lsblk).
Userdata/secrets/flake.nix are real files in tmpdir, Redis is the real
VM instance.
"""

# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

import pytest

from selfprivacy_api.jobs import Jobs
from selfprivacy_api.services.flake_service_manager import FlakeServiceManager
from selfprivacy_api.utils import UserDataFiles, WriteUserData
from selfprivacy_api.utils.block_devices import BlockDevices

# Realistic lsblk capture: root partition sda1 (uuid ec80c004-...), one
# volume sdb (uuid fa9d0026-..., mounted at /volumes/sdb), plus unusable
# sda14/sda15/sr0 entries.
from tests.test_block_device_utils import FULL_LSBLK_OUTPUT

ROOT_UUID = "ec80c004-baec-4a2c-851d-0e1807135511"

# Usernames present in tests/data/turned_on.json
PRIMARY_USER = "tester"
NORMAL_USERS = ["user1", "user2", "user3"]
ALL_USERS = NORMAL_USERS + [PRIMARY_USER]


def sp_module_url(name: str, ref: str = "flakes") -> str:
    return (
        "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git"
        f"?ref={ref}&dir=sp-modules/{name}"
    )


BASE_SERVICES = [
    "bitwarden",
    "gitea",
    "jitsi-meet",
    "nextcloud",
    "ocserv",
    "pleroma",
    "simple-nixos-mailserver",
]

FLAKE_ALL_SERVICES = {
    name: sp_module_url(name) for name in BASE_SERVICES + ["roundcube", "monitoring"]
}


def flake_content(services: dict) -> str:
    """Render a flake.nix in the same shape FlakeServiceManager writes."""
    lines = [
        "{",
        '  description = "SelfPrivacy NixOS PoC modules/extensions/bundles/packages/etc";',
        "",
    ]
    for name, url in services.items():
        lines.append(f'  inputs.{name}.url = "{url}";')
    lines.append("  outputs = _: { };")
    lines.append("}")
    return "\n".join(lines) + "\n"


async def read_flake_services() -> dict:
    async with FlakeServiceManager() as manager:
        return dict(manager.services)


@pytest.fixture
def flake_file(mocker, tmp_path):
    """Return an installer writing a flake.nix into tmpdir and pointing
    FLAKE_CONFIG_PATH (as looked up by FlakeServiceManager) at it."""

    def install(services: dict) -> str:
        flake_path = tmp_path / "flake.nix"
        flake_path.write_text(flake_content(services))
        mocker.patch(
            "selfprivacy_api.services.flake_service_manager.FLAKE_CONFIG_PATH",
            new=str(flake_path),
        )
        return str(flake_path)

    return install


@pytest.fixture
def block_devices(mocker, generic_userdata):
    """Fake the lsblk boundary with a realistic capture and refresh the
    BlockDevices singleton. Depends on generic_userdata because root
    canonical-name resolution reads userdata."""
    mock = mocker.patch(
        "subprocess.check_output", autospec=True, return_value=FULL_LSBLK_OUTPUT
    )
    BlockDevices().update()
    return mock


@pytest.fixture
def jobs():
    # Same reset pattern as tests/test_jobs.py
    j = Jobs()
    j.reset()
    assert j.get_jobs() == []
    yield j
    j.reset()


def set_api_secret(key, value) -> None:
    """Set secrets.json api.<key> = <value> through the real write path."""
    with WriteUserData(UserDataFiles.SECRETS) as secrets:
        secrets.setdefault("api", {})[key] = value
