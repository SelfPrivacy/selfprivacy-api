"""Class representing Bitwarden service"""

import base64
import subprocess
from typing import List

from selfprivacy_api.utils import ReadUserData, WriteUserData

from selfprivacy_api.utils.systemd import get_service_status
from selfprivacy_api.services.service import Service, ServiceStatus
from selfprivacy_api.services.forgejo.icon import FORGEJO_ICON
from selfprivacy_api.services.config_item import (
    StringServiceConfigItem,
    BoolServiceConfigItem,
    EnumServiceConfigItem,
    ServiceConfigItem,
)
from selfprivacy_api.utils.regex_strings import SUBDOMAIN_REGEX


class Forgejo(Service):
    """Class representing Forgejo service.

    Previously was Gitea, so some IDs are still called gitea for compatibility.
    """

    config_items: dict[str, ServiceConfigItem] = {
        "subdomain": StringServiceConfigItem(
            id="subdomain",
            default_value="git",
            description="Subdomain",
            regex=SUBDOMAIN_REGEX,
            widget="subdomain",
        ),
        "appName": StringServiceConfigItem(
            id="appName",
            default_value="SelfPrivacy git Service",
            description="The name displayed in the web interface",
        ),
        "enableLfs": BoolServiceConfigItem(
            id="enableLfs",
            default_value=True,
            description="Enable Git LFS",
        ),
        "forcePrivate": BoolServiceConfigItem(
            id="forcePrivate",
            default_value=False,
            description="Force all new repositories to be private",
        ),
        "disableRegistration": BoolServiceConfigItem(
            id="disableRegistration",
            default_value=False,
            description="Disable registration of new users",
        ),
        "requireSigninView": BoolServiceConfigItem(
            id="requireSigninView",
            default_value=False,
            description="Force users to log in to view any page",
        ),
        "defaultTheme": EnumServiceConfigItem(
            id="defaultTheme",
            default_value="forgejo-auto",
            description="Default theme",
            options=[
                "forgejo-auto",
                "forgejo-light",
                "forgejo-dark",
                "auto",
                "gitea",
                "arc-green",
            ],
        ),
    }

    @staticmethod
    def get_id() -> str:
        """Return service id. For compatibility keep in gitea."""
        return "gitea"

    @staticmethod
    def get_display_name() -> str:
        """Return service display name."""
        return "Forgejo"

    @staticmethod
    def get_description() -> str:
        """Return service description."""
        return "Forgejo is a Git forge."

    @staticmethod
    def get_svg_icon() -> str:
        """Read SVG icon from file and return it as base64 encoded string."""
        return base64.b64encode(FORGEJO_ICON.encode("utf-8")).decode("utf-8")

    @staticmethod
    def is_movable() -> bool:
        return True

    @staticmethod
    def is_required() -> bool:
        return False

    @staticmethod
    def get_backup_description() -> str:
        return "Git repositories, database and user data."

    @staticmethod
    def get_status() -> ServiceStatus:
        """
        Return Gitea status from systemd.
        Use command return code to determine status.
        Return code 0 means service is running.
        Return code 1 or 2 means service is in error stat.
        Return code 3 means service is stopped.
        Return code 4 means service is off.
        """
        return get_service_status("forgejo.service")

    @staticmethod
    def stop():
        subprocess.run(["systemctl", "stop", "forgejo.service"])

    @staticmethod
    def start():
        subprocess.run(["systemctl", "start", "forgejo.service"])

    @staticmethod
    def restart():
        subprocess.run(["systemctl", "restart", "forgejo.service"])

    @staticmethod
    def get_logs():
        return ""

    @staticmethod
    def get_folders() -> List[str]:
        """The data folder is still called gitea for compatibility."""
        return ["/var/lib/gitea"]
