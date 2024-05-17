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


with FlakeConfigManager() as manager:
    manager.services = {
        "bitwarden": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/bitwarden",
        "gitea": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/gitea",
        "jitsi-meet": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/jitsi-meet",
        "nextcloud": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/nextcloud",
        "ocserv": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/ocserv",
        "pleroma": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/pleroma",
        "simple-nixos-mailserver": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/simple-nixos-mailserver",
    }
