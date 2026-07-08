import aiofiles
import pytest

from selfprivacy_api.services.flake_service_manager import FlakeServiceManager

all_services_file = """
{
  description = "SelfPrivacy NixOS PoC modules/extensions/bundles/packages/etc";


  inputs.bitwarden.url = "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/bitwarden";

  inputs.gitea.url = "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/gitea";

  inputs.jitsi-meet.url = "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/jitsi-meet";

  inputs.nextcloud.url = "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/nextcloud";

  inputs.ocserv.url = "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/ocserv";

  inputs.pleroma.url = "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/pleroma";

  inputs.simple-nixos-mailserver.url = "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/simple-nixos-mailserver";

  outputs = _: { };
}
"""


some_services_file = """
{
  description = "SelfPrivacy NixOS PoC modules/extensions/bundles/packages/etc";


  inputs.bitwarden.url = "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/bitwarden";

  inputs.gitea.url = "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/gitea";

  inputs.jitsi-meet.url = "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/jitsi-meet";

  outputs = _: { };
}
"""


@pytest.fixture
def all_services_old_flake_mock(mocker, datadir):
    flake_config_path = datadir / "all_services_old.nix"
    mocker.patch(
        "selfprivacy_api.services.flake_service_manager.FLAKE_CONFIG_PATH",
        new=flake_config_path,
    )
    return flake_config_path


@pytest.fixture
def some_services_flake_mock(mocker, datadir):
    flake_config_path = datadir / "some_services.nix"
    mocker.patch(
        "selfprivacy_api.services.flake_service_manager.FLAKE_CONFIG_PATH",
        new=flake_config_path,
    )
    return flake_config_path


@pytest.fixture
def no_services_flake_mock(mocker, datadir):
    flake_config_path = datadir / "no_services.nix"
    mocker.patch(
        "selfprivacy_api.services.flake_service_manager.FLAKE_CONFIG_PATH",
        new=flake_config_path,
    )
    return flake_config_path


# ---


async def test_read_services_list(some_services_flake_mock):
    async with FlakeServiceManager() as manager:
        services = {
            "bitwarden": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/bitwarden",
            "gitea": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/gitea",
            "jitsi-meet": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/jitsi-meet",
        }
        assert manager.services == services


async def test_change_services_list(some_services_flake_mock):
    services = {
        "bitwarden": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/bitwarden",
        "gitea": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/gitea",
        "jitsi-meet": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/jitsi-meet",
        "nextcloud": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/nextcloud",
        "ocserv": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/ocserv",
        "pleroma": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/pleroma",
        "simple-nixos-mailserver": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/simple-nixos-mailserver",
    }

    async with FlakeServiceManager() as manager:
        manager.services = services

    async with FlakeServiceManager() as manager:
        assert manager.services == services

    async with aiofiles.open(some_services_flake_mock, "r", encoding="utf-8") as file:
        file_content = (await file.read()).strip()

    assert all_services_file.strip() == file_content


async def test_read_empty_services_list(no_services_flake_mock):
    async with FlakeServiceManager() as manager:
        services = {}
        assert manager.services == services


async def test_change_empty_services_list(no_services_flake_mock):
    services = {
        "bitwarden": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/bitwarden",
        "gitea": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/gitea",
        "jitsi-meet": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/jitsi-meet",
        "nextcloud": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/nextcloud",
        "ocserv": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/ocserv",
        "pleroma": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/pleroma",
        "simple-nixos-mailserver": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/simple-nixos-mailserver",
    }

    async with FlakeServiceManager() as manager:
        manager.services = services

    async with FlakeServiceManager() as manager:
        assert manager.services == services

    async with aiofiles.open(no_services_flake_mock, "r", encoding="utf-8") as file:
        file_content = (await file.read()).strip()

    assert all_services_file.strip() == file_content


async def test_migrate_services_list(all_services_old_flake_mock):
    async with FlakeServiceManager():
        pass

    async with aiofiles.open(
        all_services_old_flake_mock, "r", encoding="utf-8"
    ) as file:
        file_content = (await file.read()).strip()

    assert all_services_file.strip() == file_content
