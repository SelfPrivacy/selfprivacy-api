"""Class representing Nextcloud service."""
import base64
import subprocess
from typing import List

from selfprivacy_api.utils.systemd import get_service_status
from selfprivacy_api.services.service import Service, ServiceStatus

from selfprivacy_api.services.nextcloud.icon import NEXTCLOUD_ICON
from selfprivacy_api.services.config_item import (
    StringServiceConfigItem,
    ServiceConfigItem,
)
from selfprivacy_api.utils.regex_strings import SUBDOMAIN_REGEX


class Nextcloud(Service):
    """Class representing Nextcloud service."""

    config_items: dict[str, ServiceConfigItem] = {
        "subdomain": StringServiceConfigItem(
            id="subdomain",
            default_value="cloud",
            description="Subdomain",
            regex=SUBDOMAIN_REGEX,
            widget="subdomain",
        ),
    }

    @staticmethod
    def get_id() -> str:
        """Return service id."""
        return "nextcloud"

    @staticmethod
    def get_display_name() -> str:
        """Return service display name."""
        return "Nextcloud"

    @staticmethod
    def get_description() -> str:
        """Return service description."""
        return "Nextcloud is a cloud storage service that offers a web interface and a desktop client."

    @staticmethod
    def get_svg_icon() -> str:
        """Read SVG icon from file and return it as base64 encoded string."""
        return base64.b64encode(NEXTCLOUD_ICON.encode("utf-8")).decode("utf-8")

    @staticmethod
    def is_movable() -> bool:
        return True

    @staticmethod
    def is_required() -> bool:
        return False

    @staticmethod
    def get_backup_description() -> str:
        return "All the files and other data stored in Nextcloud."

    @staticmethod
    def get_status() -> ServiceStatus:
        """
        Return Nextcloud status from systemd.
        Use command return code to determine status.

        Return code 0 means service is running.
        Return code 1 or 2 means service is in error stat.
        Return code 3 means service is stopped.
        Return code 4 means service is off.
        """
        return get_service_status("phpfpm-nextcloud.service")

    @staticmethod
    def stop():
        """Stop Nextcloud service."""
        subprocess.Popen(["systemctl", "stop", "phpfpm-nextcloud.service"])

    @staticmethod
    def start():
        """Start Nextcloud service."""
        subprocess.Popen(["systemctl", "start", "phpfpm-nextcloud.service"])

    @staticmethod
    def restart():
        """Restart Nextcloud service."""
        subprocess.Popen(["systemctl", "restart", "phpfpm-nextcloud.service"])

    @staticmethod
    def get_logs():
        """Return Nextcloud logs."""
        return ""

    @staticmethod
    def get_folders() -> List[str]:
        return ["/var/lib/nextcloud"]
