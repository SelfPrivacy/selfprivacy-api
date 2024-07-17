"""Class representing Nextcloud service."""

import base64
import subprocess
from typing import Optional, List

from selfprivacy_api.services.owned_path import OwnedPath
from selfprivacy_api.utils.systemd import get_service_status
from selfprivacy_api.services.service import Service, ServiceStatus

from selfprivacy_api.services.prometheus.icon import PROMETHEUS_ICON


class Prometheus(Service):
    """Class representing Pleroma service."""

    @staticmethod
    def get_id() -> str:
        return "prometheus"

    @staticmethod
    def get_display_name() -> str:
        return "Prometheus"

    @staticmethod
    def get_description() -> str:
        return "Prometheus is a free software application used for event monitoring and alerting."

    @staticmethod
    def get_svg_icon() -> str:
        return base64.b64encode(PROMETHEUS_ICON.encode("utf-8")).decode("utf-8")

    @staticmethod
    def get_url() -> Optional[str]:
        """Return service url."""
        return None

    @staticmethod
    def get_subdomain() -> Optional[str]:
        return None

    @staticmethod
    def is_movable() -> bool:
        return False

    @staticmethod
    def is_required() -> bool:
        return True

    @staticmethod
    def get_backup_description() -> str:
        return "For Prometheus backups are not available."

    @staticmethod
    def get_status() -> ServiceStatus:
        return get_service_status("prometheus.service")

    @staticmethod
    def stop():
        subprocess.run(["systemctl", "stop", "prometheus.service"])

    @staticmethod
    def start():
        subprocess.run(["systemctl", "start", "prometheus.service"])

    @staticmethod
    def restart():
        subprocess.run(["systemctl", "restart", "prometheus.service"])

    @staticmethod
    def get_configuration(config_items):
        return {}

    @staticmethod
    def set_configuration(config_items):
        return super().set_configuration(config_items)

    @staticmethod
    def get_logs():
        return ""

    @staticmethod
    def get_owned_folders() -> List[OwnedPath]:
        return [
            OwnedPath(
                path="/var/lib/prometheus",
                owner="prometheus",
                group="prometheus",
            ),
        ]
