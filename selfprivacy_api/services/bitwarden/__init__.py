"""Class representing Bitwarden service"""
import base64
import subprocess
import typing

from selfprivacy_api.jobs import Job, JobStatus, Jobs
from selfprivacy_api.services.generic_service_mover import FolderMoveNames, move_service
from selfprivacy_api.services.generic_size_counter import get_storage_usage
from selfprivacy_api.services.generic_status_getter import get_service_status
from selfprivacy_api.services.service import Service, ServiceDnsRecord, ServiceStatus
from selfprivacy_api.utils import ReadUserData, WriteUserData, get_domain
from selfprivacy_api.utils.block_devices import BlockDevice
from selfprivacy_api.utils.huey import huey
from selfprivacy_api.utils.localization import Localization as L10n
import selfprivacy_api.utils.network as network_utils
from selfprivacy_api.services.bitwarden.icon import BITWARDEN_ICON


class Bitwarden(Service):
    """Class representing Bitwarden service."""

    @staticmethod
    def get_id() -> str:
        """Return service id."""
        return "bitwarden"

    @staticmethod
    def get_display_name(locale: str = "en") -> str:
        """Return service display name."""
        return L10n().get("services.bitwarden.display_name", locale)

    @staticmethod
    def get_description(locale: str = "en") -> str:
        """Return service description."""
        return L10n().get("services.bitwarden.description", locale)

    @staticmethod
    def get_svg_icon() -> str:
        """Read SVG icon from file and return it as base64 encoded string."""
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
        with ReadUserData() as user_data:
            return user_data.get("bitwarden", {}).get("enable", False)

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
    def enable():
        """Enable Bitwarden service."""
        with WriteUserData() as user_data:
            if "bitwarden" not in user_data:
                user_data["bitwarden"] = {}
            user_data["bitwarden"]["enable"] = True

    @staticmethod
    def disable():
        """Disable Bitwarden service."""
        with WriteUserData() as user_data:
            if "bitwarden" not in user_data:
                user_data["bitwarden"] = {}
            user_data["bitwarden"]["enable"] = False

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
        storage_usage += get_storage_usage("/var/lib/bitwarden")
        storage_usage += get_storage_usage("/var/lib/bitwarden_rs")
        return storage_usage

    @staticmethod
    def get_drive() -> str:
        with ReadUserData() as user_data:
            if user_data.get("useBinds", False):
                return user_data.get("bitwarden", {}).get("location", "sda1")
            else:
                return "sda1"

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

    def move_to_volume(self, volume: BlockDevice, locale: str = "en") -> Job:
        job = Jobs.add(
            type_id="services.bitwarden.move",
            name=L10n().get("services.bitwarden.move_job.name", locale),
            description=L10n()
            .get("services.bitwarden.move_job.description")
            .format(volume=volume.name),
        )

        move_service(
            self,
            volume,
            job,
            [
                FolderMoveNames(
                    name="bitwarden",
                    bind_location="/var/lib/bitwarden",
                    group="vaultwarden",
                    owner="vaultwarden",
                ),
                FolderMoveNames(
                    name="bitwarden_rs",
                    bind_location="/var/lib/bitwarden_rs",
                    group="vaultwarden",
                    owner="vaultwarden",
                ),
            ],
            "bitwarden",
        )

        return job
