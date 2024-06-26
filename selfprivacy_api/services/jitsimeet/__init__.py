"""Class representing Jitsi Meet service"""
import base64
import subprocess
from typing import Optional, List

from selfprivacy_api.jobs import Job
from selfprivacy_api.utils.systemd import (
    get_service_status_from_several_units,
)
from selfprivacy_api.services.service import Service, ServiceStatus
from selfprivacy_api.utils import get_domain
from selfprivacy_api.utils.block_devices import BlockDevice
from selfprivacy_api.services.jitsimeet.icon import JITSI_ICON


class JitsiMeet(Service):
    """Class representing Jitsi service"""

    @staticmethod
    def get_id() -> str:
        """Return service id."""
        return "jitsi-meet"

    @staticmethod
    def get_display_name() -> str:
        """Return service display name."""
        return "JitsiMeet"

    @staticmethod
    def get_description() -> str:
        """Return service description."""
        return "Jitsi Meet is a free and open-source video conferencing solution."

    @staticmethod
    def get_svg_icon() -> str:
        """Read SVG icon from file and return it as base64 encoded string."""
        return base64.b64encode(JITSI_ICON.encode("utf-8")).decode("utf-8")

    @staticmethod
    def get_url() -> Optional[str]:
        """Return service url."""
        domain = get_domain()
        return f"https://meet.{domain}"

    @staticmethod
    def get_subdomain() -> Optional[str]:
        return "meet"

    @staticmethod
    def is_movable() -> bool:
        return False

    @staticmethod
    def is_required() -> bool:
        return False

    @staticmethod
    def get_backup_description() -> str:
        return "Secrets that are used to encrypt the communication."

    @staticmethod
    def get_status() -> ServiceStatus:
        return get_service_status_from_several_units(
            ["jitsi-videobridge.service", "jicofo.service"]
        )

    @staticmethod
    def stop():
        subprocess.run(
            ["systemctl", "stop", "jitsi-videobridge.service"],
            check=False,
        )
        subprocess.run(["systemctl", "stop", "jicofo.service"], check=False)

    @staticmethod
    def start():
        subprocess.run(
            ["systemctl", "start", "jitsi-videobridge.service"],
            check=False,
        )
        subprocess.run(["systemctl", "start", "jicofo.service"], check=False)

    @staticmethod
    def restart():
        subprocess.run(
            ["systemctl", "restart", "jitsi-videobridge.service"],
            check=False,
        )
        subprocess.run(["systemctl", "restart", "jicofo.service"], check=False)

    @staticmethod
    def get_configuration():
        return {}

    @staticmethod
    def set_configuration(config_items):
        return super().set_configuration(config_items)

    @staticmethod
    def get_logs():
        return ""

    @staticmethod
    def get_folders() -> List[str]:
        return ["/var/lib/jitsi-meet"]

    def move_to_volume(self, volume: BlockDevice) -> Job:
        raise NotImplementedError("jitsi-meet service is not movable")
