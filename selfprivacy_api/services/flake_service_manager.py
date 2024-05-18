import re
from typing import Dict, Tuple, Optional

FLAKE_CONFIG_PATH = "/etc/nixos/sp-modules/flake.nix"


class FlakeServiceManager:
    def __enter__(self) -> "FlakeServiceManager":
        self.services = {}

        with open(FLAKE_CONFIG_PATH, "r") as file:
            for line in file:
                service_name, url = self._extract_services(input_string=line)
                if service_name and url:
                    self.services[service_name] = url

        return self

    def _extract_services(
        self, input_string: str
    ) -> Tuple[Optional[str], Optional[str]]:
        pattern = r"inputs\.(\w+)\.url\s*=\s*(\S+);"
        match = re.search(pattern, input_string)

        if match:
            variable_name = match.group(1)
            url = match.group(2)
            return variable_name, url
        else:
            return None, None

    def __exit__(self, exc_type, exc_value, traceback) -> None:
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
    outputs = _: { };
}
"""
            )


if __name__ == "__main__":
    with FlakeServiceManager() as manager:
        # manager.services = {
        #     "bitwarden": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/bitwarden",
        #     "gitea": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/gitea",
        #     "jitsi-meet": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/jitsi-meet",
        #     "nextcloud": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/nextcloud",
        #     "ocserv": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/ocserv",
        #     "pleroma": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/pleroma",
        #     "simple-nixos-mailserver": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/simple-nixos-mailserver",
        # }
        print(manager.services)
