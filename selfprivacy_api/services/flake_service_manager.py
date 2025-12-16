import copy

from opentelemetry import trace
from selfprivacy_api.utils.nix import evaluate_nix_file, to_nix_expr, format_nix_expr

FLAKE_CONFIG_PATH = "/etc/nixos/flake.nix"
SP_MODULE_INPUT_PREFIX = "sp-module-"


tracer = trace.get_tracer(__name__)


class FlakeServiceManager:
    async def __aenter__(self) -> "FlakeServiceManager":
        self._span = tracer.start_span("FlakeServiceManager context")
        self._inputs = {}
        self._services = {}

        inputs = await evaluate_nix_file(
            FLAKE_CONFIG_PATH, 'f: if builtins.hasAttr "inputs" f then f.inputs else {}'
        )

        for key, value in inputs.items():
            if key.startswith(SP_MODULE_INPUT_PREFIX):
                service_name = key.removeprefix(SP_MODULE_INPUT_PREFIX)
                self._services[service_name] = value["url"]
            else:
                self._inputs[key] = value

        self.inputs = copy.deepcopy(self._inputs)
        self.services = copy.deepcopy(self._services)

        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        if self.inputs == self._inputs and self.services == self._services:
            return

        inputs = self.inputs
        for service_name, url in self.services.items():
            inputs[f"{SP_MODULE_INPUT_PREFIX}{service_name}"] = {"url": url}

        inputs_expr = await to_nix_expr(inputs)

        content = """{
  description = "SelfPrivacy NixOS configuration local flake";
"""
        content += f"\n  inputs = {inputs_expr};"
        content += """
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

        content = await format_nix_expr(content)

        with open(FLAKE_CONFIG_PATH, "w") as file:
            file.write(content)

        if exc:
            self._span.set_status(trace.Status(trace.StatusCode.ERROR))
            self._span.record_exception(exc)
        else:
            self._span.set_status(trace.Status(trace.StatusCode.OK))

        self._span.end()
