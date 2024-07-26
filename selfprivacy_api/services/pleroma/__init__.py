"""Class representing Nextcloud service."""

import base64
import subprocess
from typing import List

from selfprivacy_api.services.owned_path import OwnedPath
from selfprivacy_api.utils.systemd import get_service_status
from selfprivacy_api.services.service import Service, ServiceStatus

from selfprivacy_api.services.pleroma.icon import PLEROMA_ICON


class Pleroma(Service):
    """Class representing Pleroma service."""

    @staticmethod
    def get_id() -> str:
        return "pleroma"

    @staticmethod
    def get_display_name() -> str:
        return "Pleroma"

    @staticmethod
    def get_description() -> str:
        return "Pleroma is a microblogging service that offers a web interface and a desktop client."

    @staticmethod
    def get_svg_icon() -> str:
        return base64.b64encode(PLEROMA_ICON.encode("utf-8")).decode("utf-8")

    @staticmethod
    def is_movable() -> bool:
        return True

    @staticmethod
    def is_required() -> bool:
        return False

    @staticmethod
    def get_backup_description() -> str:
        return "Your Pleroma accounts, posts and media."

    @staticmethod
    def get_status() -> ServiceStatus:
        return get_service_status("pleroma.service")

    @staticmethod
    def stop():
        subprocess.run(["systemctl", "stop", "pleroma.service"])
        subprocess.run(["systemctl", "stop", "postgresql.service"])

    @staticmethod
    def start():
        subprocess.run(["systemctl", "start", "pleroma.service"])
        subprocess.run(["systemctl", "start", "postgresql.service"])

    @staticmethod
    def restart():
        subprocess.run(["systemctl", "restart", "pleroma.service"])
        subprocess.run(["systemctl", "restart", "postgresql.service"])

    @classmethod
    def get_configuration(cls):
        return {}

    @classmethod
    def set_configuration(cls, config_items):
        return super().set_configuration(config_items)

    @staticmethod
    def get_logs():
        return ""

    @staticmethod
    def get_owned_folders() -> List[OwnedPath]:
        """
        Get a list of occupied directories with ownership info
        Pleroma has folders that are owned by different users
        """
        return [
            OwnedPath(
                path="/var/lib/pleroma",
                owner="pleroma",
                group="pleroma",
            ),
            OwnedPath(
                path="/var/lib/postgresql",
                owner="postgres",
                group="postgres",
            ),
        ]
