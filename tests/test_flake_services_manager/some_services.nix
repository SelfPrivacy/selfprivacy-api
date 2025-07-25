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
