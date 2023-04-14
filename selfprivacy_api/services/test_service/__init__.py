"""Class representing Bitwarden service"""
import base64
import typing
from typing import List

from selfprivacy_api.jobs import Job
from selfprivacy_api.services.service import Service, ServiceDnsRecord, ServiceStatus
from selfprivacy_api.utils import ReadUserData, get_domain
from selfprivacy_api.utils.block_devices import BlockDevice
import selfprivacy_api.utils.network as network_utils

from selfprivacy_api.services.test_service.icon import BITWARDEN_ICON


class DummyService(Service):
    """A test service"""

    def __init_subclass__(cls, location):
        cls.location = location

    @staticmethod
    def get_id() -> str:
        """Return service id."""
        return "testservice"

    @staticmethod
    def get_display_name() -> str:
        """Return service display name."""
        return "Test Service"

    @staticmethod
    def get_description() -> str:
        """Return service description."""
        return "A small service used for test purposes. Does nothing."

    @staticmethod
    def get_svg_icon() -> str:
        """Read SVG icon from file and return it as base64 encoded string."""
        # return ""
        return base64.b64encode(BITWARDEN_ICON.encode("utf-8")).decode("utf-8")

    @staticmethod
    def get_url() -> typing.Optional[str]:
        """Return service url."""
        domain = get_domain()
        return f"https://password.{domain}"

    @staticmethod
    def is_movable() -> bool:
        return True

    @staticmethod
    def is_required() -> bool:
        return False

    @staticmethod
    def is_enabled() -> bool:
        return True

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
        return 0

    @staticmethod
    def enable():
        pass

    @staticmethod
    def disable():
        pass

    @staticmethod
    def stop():
        pass

    @staticmethod
    def start():
        pass

    @staticmethod
    def restart():
        pass

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
        return storage_usage

    @staticmethod
    def get_drive(cls) -> str:
        return "sda1"

    @classmethod
    def get_folders(cls) -> List[str]:
        return [cls.location]

    @staticmethod
    def get_dns_records() -> typing.List[ServiceDnsRecord]:
        """Return list of DNS records for Bitwarden service."""
        return [
            ServiceDnsRecord(
                type="A",
                name="password",
                content=network_utils.get_ip4(),
                ttl=3600,
            ),
            ServiceDnsRecord(
                type="AAAA",
                name="password",
                content=network_utils.get_ip6(),
                ttl=3600,
            ),
        ]

    def move_to_volume(self, volume: BlockDevice) -> Job:
        pass
