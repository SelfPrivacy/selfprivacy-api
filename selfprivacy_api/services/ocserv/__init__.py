"""Class representing ocserv service."""
import base64
import subprocess
import typing
from selfprivacy_api.jobs import Job, Jobs
from selfprivacy_api.services.generic_service_mover import FolderMoveNames, move_service
from selfprivacy_api.services.generic_status_getter import get_service_status
from selfprivacy_api.services.service import Service, ServiceDnsRecord, ServiceStatus
from selfprivacy_api.utils import ReadUserData, WriteUserData
from selfprivacy_api.utils.block_devices import BlockDevice
from selfprivacy_api.services.ocserv.icon import OCSERV_ICON
import selfprivacy_api.utils.network as network_utils


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

    @staticmethod
    def get_url() -> typing.Optional[str]:
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
    def is_enabled() -> bool:
        with ReadUserData() as user_data:
            return user_data.get("ocserv", {}).get("enable", False)

    @staticmethod
    def get_status() -> ServiceStatus:
        return get_service_status("ocserv.service")

    @staticmethod
    def enable():
        with WriteUserData() as user_data:
            if "ocserv" not in user_data:
                user_data["ocserv"] = {}
            user_data["ocserv"]["enable"] = True

    @staticmethod
    def disable():
        with WriteUserData() as user_data:
            if "ocserv" not in user_data:
                user_data["ocserv"] = {}
            user_data["ocserv"]["enable"] = False

    @staticmethod
    def stop():
        subprocess.run(["systemctl", "stop", "ocserv.service"])

    @staticmethod
    def start():
        subprocess.run(["systemctl", "start", "ocserv.service"])

    @staticmethod
    def restart():
        subprocess.run(["systemctl", "restart", "ocserv.service"])

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
    def get_drive() -> str:
        return "sda1"

    @staticmethod
    def get_dns_records() -> typing.List[ServiceDnsRecord]:
        return [
            ServiceDnsRecord(
                type="A",
                name="vpn",
                content=network_utils.get_ip4(),
                ttl=3600,
            ),
            ServiceDnsRecord(
                type="AAAA",
                name="vpn",
                content=network_utils.get_ip6(),
                ttl=3600,
            ),
        ]

    @staticmethod
    def get_folders() -> typing.List[str]:
        return []

    def move_to_volume(self, volume: BlockDevice) -> Job:
        raise NotImplementedError("ocserv service is not movable")
