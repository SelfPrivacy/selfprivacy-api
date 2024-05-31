import re
from typing import Tuple, Optional

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
        pattern = r"inputs\.([\w-]+)\.url\s*=\s*([\S]+);"
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
