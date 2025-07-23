import re
from typing import Tuple, Optional
from selfprivacy_api.utils.nix import evaluate_nix_file, to_nix_expr, format_nix_expr

FLAKE_CONFIG_PATH = "/etc/nixos/flake.nix"
SP_MODULE_INPUT_PREFIX = "sp-module-"


class FlakeServiceManager:
    def __enter__(self) -> "FlakeServiceManager":
        self.services = {}

        inputs = evaluate_nix_file(FLAKE_CONFIG_PATH, "f: f.inputs")

        for key, value in inputs.items():
            if key.startswith(SP_MODULE_INPUT_PREFIX):
                service_name = key.removeprefix(SP_MODULE_INPUT_PREFIX)
                self.services[service_name] = value["url"]

        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        inputs = {}
        inputs["selfprivacy-nixos-config"] = {
            # TODO: make it configurable
            "url": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes",
            "inputs": {"selfprivacy-api": {"follows": "sp-api"}},
        }
        inputs["sp-api"] = {
            "url": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-rest-api?ref=nhnn/sp-modules-flake-merge",
            "inputs": {"nixpkgs": {"follows": "selfprivacy-nixos-config/nixpkgs"}},
        }
        for service_name, url in self.services.items():
            inputs[f"{SP_MODULE_INPUT_PREFIX}{service_name}"] = {"url": url}

        inputs_expr = to_nix_expr(inputs)

        content = """{
  description = "SelfPrivacy NixOS configuration local flake";
"""
        content += f"\n  inputs = {inputs_expr};\n"
        content += """
  outputs = inputs@{ self, selfprivacy-nixos-config, ... }: let
    lib = selfprivacy-nixos-config.inputs.nixpkgs.lib;
  in {
    nixosConfigurations =
      selfprivacy-nixos-config.outputs.nixosConfigurations-fun {
        hardware-configuration = ./hardware-configuration.nix;
        deployment = ./deployment.nix;
        userdata = builtins.fromJSON (builtins.readFile ./userdata.json);
        top-level-flake = self;
        sp-modules = lib.mapAttrs'
          (service: value: { name = lib.removePrefix "sp-module-" service; inherit value; })
          (lib.filterAttrs (k: _: lib.hasPrefix "sp-module-" k) inputs);
      };
  };
}
"""

        content = format_nix_expr(content)

        with open(FLAKE_CONFIG_PATH, "w") as file:
            file.write(content)
