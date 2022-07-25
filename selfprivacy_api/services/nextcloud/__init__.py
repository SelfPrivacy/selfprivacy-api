"""Class representing Nextcloud service."""
import base64
import subprocess
import psutil
from selfprivacy_api.services.service import Service, ServiceStatus
from selfprivacy_api.utils import ReadUserData, WriteUserData


class Nextcloud(Service):
    """Class representing Nextcloud service."""

    def get_id(self) -> str:
        """Return service id."""
        return "nextcloud"

    def get_display_name(self) -> str:
        """Return service display name."""
        return "Nextcloud"

    def get_description(self) -> str:
        """Return service description."""
        return "Nextcloud is a cloud storage service that offers a web interface and a desktop client."

    def get_svg_icon(self) -> str:
        """Read SVG icon from file and return it as base64 encoded string."""
        with open("selfprivacy_api/services/nextcloud/nextcloud.svg", "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def is_enabled(self) -> bool:
        with ReadUserData() as user_data:
            return user_data.get("nextcloud", {}).get("enable", False)

    def get_status(self) -> ServiceStatus:
        """
        Return Nextcloud status from systemd.
        Use command return code to determine status.

        Return code 0 means service is running.
        Return code 1 or 2 means service is in error stat.
        Return code 3 means service is stopped.
        Return code 4 means service is off.
        """
        service_status = subprocess.Popen(
            ["systemctl", "status", "phpfpm-nextcloud.service"]
        )
        service_status.communicate()[0]
        if service_status.returncode == 0:
            return ServiceStatus.RUNNING
        elif service_status.returncode == 1 or service_status.returncode == 2:
            return ServiceStatus.ERROR
        elif service_status.returncode == 3:
            return ServiceStatus.STOPPED
        elif service_status.returncode == 4:
            return ServiceStatus.OFF
        else:
            return ServiceStatus.DEGRADED

    def enable(self):
        """Enable Nextcloud service."""
        with WriteUserData() as user_data:
            if "nextcloud" not in user_data:
                user_data["nextcloud"] = {}
            user_data["nextcloud"]["enable"] = True

    def disable(self):
        """Disable Nextcloud service."""
        with WriteUserData() as user_data:
            if "nextcloud" not in user_data:
                user_data["nextcloud"] = {}
            user_data["nextcloud"]["enable"] = False

    def stop(self):
        """Stop Nextcloud service."""
        subprocess.Popen(["systemctl", "stop", "phpfpm-nextcloud.service"])

    def start(self):
        """Start Nextcloud service."""
        subprocess.Popen(["systemctl", "start", "phpfpm-nextcloud.service"])

    def restart(self):
        """Restart Nextcloud service."""
        subprocess.Popen(["systemctl", "restart", "phpfpm-nextcloud.service"])

    def get_configuration(self) -> dict:
        """Return Nextcloud configuration."""
        return {}

    def set_configuration(self, config_items):
        return super().set_configuration(config_items)

    def get_logs(self):
        """Return Nextcloud logs."""
        return ""

    def get_storage_usage(self):
        return psutil.disk_usage("/var/lib/nextcloud").used
