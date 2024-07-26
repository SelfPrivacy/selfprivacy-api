"""Class representing Roundcube service"""

import base64
import subprocess
from typing import List

from selfprivacy_api.jobs import Job
from selfprivacy_api.utils.systemd import (
    get_service_status_from_several_units,
)
from selfprivacy_api.services.service import Service, ServiceStatus
from selfprivacy_api.utils.block_devices import BlockDevice
from selfprivacy_api.services.roundcube.icon import ROUNDCUBE_ICON
from selfprivacy_api.services.config_item import (
    StringServiceConfigItem,
    ServiceConfigItem,
)
from selfprivacy_api.utils.regex_strings import SUBDOMAIN_REGEX


class Roundcube(Service):
    """Class representing roundcube service"""

    config_items: dict[str, ServiceConfigItem] = {
        "subdomain": StringServiceConfigItem(
            id="subdomain",
            default_value="roundcube",
            description="Subdomain",
            regex=SUBDOMAIN_REGEX,
            widget="subdomain",
        ),
    }

    @staticmethod
    def get_id() -> str:
        """Return service id."""
        return "roundcube"

    @staticmethod
    def get_display_name() -> str:
        """Return service display name."""
        return "Roundcube"

    @staticmethod
    def get_description() -> str:
        """Return service description."""
        return "Roundcube is an open source webmail software."

    @staticmethod
    def get_svg_icon() -> str:
        """Read SVG icon from file and return it as base64 encoded string."""
        return base64.b64encode(ROUNDCUBE_ICON.encode("utf-8")).decode("utf-8")

    @staticmethod
    def is_movable() -> bool:
        return False

    @staticmethod
    def is_required() -> bool:
        return False

    @staticmethod
    def can_be_backed_up() -> bool:
        return False

    @staticmethod
    def get_backup_description() -> str:
        return "Nothing to backup."

    @staticmethod
    def get_status() -> ServiceStatus:
        return get_service_status_from_several_units(["phpfpm-roundcube.service"])

    @staticmethod
    def stop():
        subprocess.run(
            ["systemctl", "stop", "phpfpm-roundcube.service"],
            check=False,
        )

    @staticmethod
    def start():
        subprocess.run(
            ["systemctl", "start", "phpfpm-roundcube.service"],
            check=False,
        )

    @staticmethod
    def restart():
        subprocess.run(
            ["systemctl", "restart", "phpfpm-roundcube.service"],
            check=False,
        )

    @staticmethod
    def get_logs():
        return ""

    @staticmethod
    def get_folders() -> List[str]:
        return []

    def move_to_volume(self, volume: BlockDevice) -> Job:
        raise NotImplementedError("roundcube service is not movable")
