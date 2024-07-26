"""Class representing ocserv service."""

import base64
import subprocess
import typing
from selfprivacy_api.jobs import Job
from selfprivacy_api.utils.systemd import get_service_status
from selfprivacy_api.services.service import Service, ServiceStatus
from selfprivacy_api.utils.block_devices import BlockDevice
from selfprivacy_api.services.ocserv.icon import OCSERV_ICON


class Ocserv(Service):
    """Class representing ocserv service."""

    @staticmethod
    def get_id() -> str:
        return "ocserv"

    @staticmethod
    def get_display_name() -> str:
        return "OpenConnect VPN"

    @staticmethod
    def get_description() -> str:
        return "OpenConnect VPN to connect your devices and access the internet."

    @staticmethod
    def get_svg_icon() -> str:
        return base64.b64encode(OCSERV_ICON.encode("utf-8")).decode("utf-8")

    @classmethod
    def get_url(cls) -> typing.Optional[str]:
        """Return service url."""
        return None

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
        return get_service_status("ocserv.service")

    @staticmethod
    def stop():
        subprocess.run(["systemctl", "stop", "ocserv.service"], check=False)

    @staticmethod
    def start():
        subprocess.run(["systemctl", "start", "ocserv.service"], check=False)

    @staticmethod
    def restart():
        subprocess.run(["systemctl", "restart", "ocserv.service"], check=False)

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
    def get_folders() -> typing.List[str]:
        return []

    def move_to_volume(self, volume: BlockDevice) -> Job:
        raise NotImplementedError("ocserv service is not movable")
