import re
from typing import Tuple, Optional

import aiofiles

FLAKE_CONFIG_PATH = "/etc/nixos/sp-modules/flake.nix"


class FlakeServiceManager:
    async def __aenter__(self) -> "FlakeServiceManager":
        self.services = {}

        async with aiofiles.open(FLAKE_CONFIG_PATH, "r") as file:
            lines = await file.readlines()

        for line in lines:
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
            if url.startswith('"') and url.endswith('"'):
                return variable_name, url[1:-1]
            return variable_name, url
        else:
            return None, None

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        async with aiofiles.open(FLAKE_CONFIG_PATH, "w") as file:
            await file.write(
                """
{
  description = "SelfPrivacy NixOS PoC modules/extensions/bundles/packages/etc";\n
"""
            )

            for key, value in self.services.items():
                await file.write(
                    f"""
  inputs.{key}.url = "{value}";
"""
                )

            await file.write(
                """
  outputs = _: { };
}
"""
            )
