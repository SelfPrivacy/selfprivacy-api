"""Class representing Jitsi service"""
import base64
import subprocess
import typing

from selfprivacy_api.jobs import Job, Jobs
from selfprivacy_api.services.generic_service_mover import FolderMoveNames, move_service
from selfprivacy_api.services.generic_size_counter import get_storage_usage
from selfprivacy_api.services.generic_status_getter import (
    get_service_status,
    get_service_status_from_several_units,
)
from selfprivacy_api.services.service import Service, ServiceDnsRecord, ServiceStatus
from selfprivacy_api.utils import ReadUserData, WriteUserData, get_domain
from selfprivacy_api.utils.block_devices import BlockDevice
from selfprivacy_api.utils.huey import huey
import selfprivacy_api.utils.network as network_utils
from selfprivacy_api.services.jitsi.icon import JITSI_ICON


class Jitsi(Service):
    """Class representing Jitsi service"""

    @staticmethod
    def get_id() -> str:
        """Return service id."""
        return "jitsi"

    @staticmethod
    def get_display_name() -> str:
        """Return service display name."""
        return "Jitsi"

    @staticmethod
    def get_description() -> str:
        """Return service description."""
        return "Jitsi is a free and open-source video conferencing solution."

    @staticmethod
    def get_svg_icon() -> str:
        """Read SVG icon from file and return it as base64 encoded string."""
        return base64.b64encode(JITSI_ICON.encode("utf-8")).decode("utf-8")

    @staticmethod
    def get_url() -> typing.Optional[str]:
        """Return service url."""
        domain = get_domain()
        return f"https://meet.{domain}"

    @staticmethod
    def is_movable() -> bool:
        return False

    @staticmethod
    def is_required() -> bool:
        return False

    @staticmethod
    def is_enabled() -> bool:
        with ReadUserData() as user_data:
            return user_data.get("jitsi", {}).get("enable", False)

    @staticmethod
    def get_status() -> ServiceStatus:
        return get_service_status_from_several_units(
            ["jitsi-videobridge.service", "jicofo.service"]
        )

    @staticmethod
    def enable():
        """Enable Jitsi service."""
        with WriteUserData() as user_data:
            if "jitsi" not in user_data:
                user_data["jitsi"] = {}
            user_data["jitsi"]["enable"] = True

    @staticmethod
    def disable():
        """Disable Gitea service."""
        with WriteUserData() as user_data:
            if "jitsi" not in user_data:
                user_data["jitsi"] = {}
            user_data["jitsi"]["enable"] = False

    @staticmethod
    def stop():
        subprocess.run(["systemctl", "stop", "jitsi-videobridge.service"])
        subprocess.run(["systemctl", "stop", "jicofo.service"])

    @staticmethod
    def start():
        subprocess.run(["systemctl", "start", "jitsi-videobridge.service"])
        subprocess.run(["systemctl", "start", "jicofo.service"])

    @staticmethod
    def restart():
        subprocess.run(["systemctl", "restart", "jitsi-videobridge.service"])
        subprocess.run(["systemctl", "restart", "jicofo.service"])

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
    def get_storage_usage() -> int:
        storage_usage = 0
        storage_usage += get_storage_usage("/var/lib/jitsi-meet")
        return storage_usage

    @staticmethod
    def get_folders() -> typing.List[str]:
        return ["/var/lib/jitsi-meet"]

    @staticmethod
    def get_drive() -> str:
        return "sda1"

    @staticmethod
    def get_dns_records() -> typing.List[ServiceDnsRecord]:
        ip4 = network_utils.get_ip4()
        ip6 = network_utils.get_ip6()
        return [
            ServiceDnsRecord(
                type="A",
                name="meet",
                content=ip4,
                ttl=3600,
            ),
            ServiceDnsRecord(
                type="AAAA",
                name="meet",
                content=ip6,
                ttl=3600,
            ),
        ]

    def move_to_volume(self, volume: BlockDevice) -> Job:
        raise NotImplementedError("jitsi service is not movable")
