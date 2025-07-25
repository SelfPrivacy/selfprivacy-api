import pytest

from selfprivacy_api.services.flake_service_manager import FlakeServiceManager

all_services_file = """
{
  description = "SelfPrivacy NixOS configuration local flake";

  inputs = {
    selfprivacy-nixos-config = {
      url = "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes";
    };
    sp-module-bitwarden = {
      url = "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/bitwarden";
    };
    sp-module-gitea = {
      url = "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/gitea";
    };
    sp-module-jitsi-meet = {
      url = "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/jitsi-meet";
    };
    sp-module-monitoring = {
      url = "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/monitoring";
    };
    sp-module-nextcloud = {
      url = "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/nextcloud";
    };
    sp-module-roundcube = {
      url = "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/roundcube";
    };
    sp-module-simple-nixos-mailserver = {
      url = "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/simple-nixos-mailserver";
    };
    sp-module-vikunja = {
      url = "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/vikunja";
    };
  };
  outputs =
    inputs@{ self, selfprivacy-nixos-config, ... }:
    let
      lib = selfprivacy-nixos-config.inputs.nixpkgs.lib;
    in
    {
      nixosConfigurations = selfprivacy-nixos-config.outputs.nixosConfigurations-fun {
        hardware-configuration = ./hardware-configuration.nix;
        deployment = ./deployment.nix;
        userdata = builtins.fromJSON (builtins.readFile ./userdata.json);
        top-level-flake = self;
        sp-modules = lib.mapAttrs' (service: value: {
          name = lib.removePrefix "sp-module-" service;
          inherit value;
        }) (lib.filterAttrs (k: _: lib.hasPrefix "sp-module-" k) inputs);
      };
    };
}
"""


some_services_file = """
{
  description = "SelfPrivacy NixOS configuration local flake";

  inputs = {
    selfprivacy-nixos-config = {
      url = "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes";
    };
    sp-module-gitea = {
      url = "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/gitea";
    };
    sp-module-jitsi-meet = {
      url = "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/jitsi-meet";
    };
    sp-module-monitoring = {
      url = "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/monitoring";
    };
  };
  outputs =
    inputs@{ self, selfprivacy-nixos-config, ... }:
    let
      lib = selfprivacy-nixos-config.inputs.nixpkgs.lib;
    in
    {
      nixosConfigurations = selfprivacy-nixos-config.outputs.nixosConfigurations-fun {
        hardware-configuration = ./hardware-configuration.nix;
        deployment = ./deployment.nix;
        userdata = builtins.fromJSON (builtins.readFile ./userdata.json);
        top-level-flake = self;
        sp-modules = lib.mapAttrs' (service: value: {
          name = lib.removePrefix "sp-module-" service;
          inherit value;
        }) (lib.filterAttrs (k: _: lib.hasPrefix "sp-module-" k) inputs);
      };
    };
}
"""


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


def test_read_services_list(some_services_flake_mock):
    with FlakeServiceManager() as manager:
        services = {
            "gitea": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/gitea",
            "jitsi-meet": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/jitsi-meet",
            "monitoring": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/monitoring",
        }
        assert manager.services == services


def test_change_services_list(some_services_flake_mock):
    services = {
        "bitwarden": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/bitwarden",
        "gitea": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/gitea",
        "jitsi-meet": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/jitsi-meet",
        "monitoring": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/monitoring",
        "nextcloud": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/nextcloud",
        "roundcube": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/roundcube",
        "simple-nixos-mailserver": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/simple-nixos-mailserver",
        "vikunja": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/vikunja",
    }

    with FlakeServiceManager() as manager:
        manager.services = services

    with FlakeServiceManager() as manager:
        assert manager.services == services

    with open(some_services_flake_mock, "r", encoding="utf-8") as file:
        file_content = file.read().strip()

    assert all_services_file.strip() == file_content


def test_read_empty_services_list(no_services_flake_mock):
    with FlakeServiceManager() as manager:
        services = {}
        assert manager.services == services


def test_change_empty_services_list(no_services_flake_mock):
    services = {
        "bitwarden": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/bitwarden",
        "gitea": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/gitea",
        "jitsi-meet": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/jitsi-meet",
        "monitoring": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/monitoring",
        "nextcloud": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/nextcloud",
        "roundcube": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/roundcube",
        "simple-nixos-mailserver": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/simple-nixos-mailserver",
        "vikunja": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/vikunja",
    }

    with FlakeServiceManager() as manager:
        manager.services = services

    with FlakeServiceManager() as manager:
        assert manager.services == services

    with open(no_services_flake_mock, "r", encoding="utf-8") as file:
        file_content = file.read().strip()

    assert all_services_file.strip() == file_content
