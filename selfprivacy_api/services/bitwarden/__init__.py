"""Class representing Bitwarden service"""
import base64
import subprocess
from typing import List

from selfprivacy_api.utils.systemd import get_service_status
from selfprivacy_api.services.service import Service, ServiceStatus
from selfprivacy_api.services.bitwarden.icon import BITWARDEN_ICON
from selfprivacy_api.services.config_item import (
    StringServiceConfigItem,
    BoolServiceConfigItem,
    ServiceConfigItem,
)
from selfprivacy_api.utils.regex_strings import SUBDOMAIN_REGEX


class Bitwarden(Service):
    """Class representing Bitwarden service."""

    config_items: dict[str, ServiceConfigItem] = {
        "subdomain": StringServiceConfigItem(
            id="subdomain",
            default_value="password",
            description="Subdomain",
            regex=SUBDOMAIN_REGEX,
            widget="subdomain",
        ),
        "signupsAllowed": BoolServiceConfigItem(
            id="signupsAllowed",
            default_value=True,
            description="Allow new user signups",
        ),
        "sendsAllowed": BoolServiceConfigItem(
            id="sendsAllowed",
            default_value=True,
            description="Allow users to use Bitwarden Send",
        ),
        "emergencyAccessAllowed": BoolServiceConfigItem(
            id="emergencyAccessAllowed",
            default_value=True,
            description="Allow users to enable Emergency Access",
        ),
    }

    @staticmethod
    def get_id() -> str:
        """Return service id."""
        return "bitwarden"

    @staticmethod
    def get_display_name() -> str:
        """Return service display name."""
        return "Bitwarden"

    @staticmethod
    def get_description() -> str:
        """Return service description."""
        return "Bitwarden is a password manager."

    @staticmethod
    def get_svg_icon() -> str:
        """Read SVG icon from file and return it as base64 encoded string."""
        return base64.b64encode(BITWARDEN_ICON.encode("utf-8")).decode("utf-8")

    @staticmethod
    def get_user() -> str:
        return "vaultwarden"

    @staticmethod
    def is_movable() -> bool:
        return True

    @staticmethod
    def is_required() -> bool:
        return False

    @staticmethod
    def get_backup_description() -> str:
        return "Password database, encryption certificate and attachments."

    @staticmethod
    def get_status() -> ServiceStatus:
        """
        Return Bitwarden status from systemd.
        Use command return code to determine status.

        Return code 0 means service is running.
        Return code 1 or 2 means service is in error stat.
        Return code 3 means service is stopped.
        Return code 4 means service is off.
        """
        return get_service_status("vaultwarden.service")

    @staticmethod
    def stop():
        subprocess.run(["systemctl", "stop", "vaultwarden.service"])

    @staticmethod
    def start():
        subprocess.run(["systemctl", "start", "vaultwarden.service"])

    @staticmethod
    def restart():
        subprocess.run(["systemctl", "restart", "vaultwarden.service"])

    @staticmethod
    def get_logs():
        return ""

    @staticmethod
    def get_folders() -> List[str]:
        return ["/var/lib/bitwarden", "/var/lib/bitwarden_rs"]
