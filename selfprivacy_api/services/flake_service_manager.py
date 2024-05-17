FLAKE_CONFIG_PATH = "/etc/nixos/sp-modules/flake.nix"


class FlakeServiceManager:
    def __enter__(self):
        self.services = {}
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        with open(FLAKE_CONFIG_PATH, "w") as file:
            file.write(
                """
{
    description = "SelfPrivacy NixOS PoC modules/extensions/bundles/packages/etc";\n
"""
            )

            for key, value in self.services.items():
                file.write(
                    f"""
    inputs.{key}.url = {value};
"""
                )

            file.write(
                """
    inputs.my.url = path:./my;
    outputs = _: { };
}
"""
            )
