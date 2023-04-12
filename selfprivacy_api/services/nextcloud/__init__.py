"""Class representing Nextcloud service."""
import base64
import subprocess
import typing
from selfprivacy_api.jobs import Job, Jobs
from selfprivacy_api.services.generic_service_mover import FolderMoveNames, move_service
from selfprivacy_api.services.generic_size_counter import get_storage_usage
from selfprivacy_api.services.generic_status_getter import get_service_status
from selfprivacy_api.services.service import Service, ServiceDnsRecord, ServiceStatus
from selfprivacy_api.utils import ReadUserData, WriteUserData, get_domain
from selfprivacy_api.utils.block_devices import BlockDevice
from selfprivacy_api.utils.localization import Localization as L10n
import selfprivacy_api.utils.network as network_utils
from selfprivacy_api.services.nextcloud.icon import NEXTCLOUD_ICON


class Nextcloud(Service):
    """Class representing Nextcloud service."""

    @staticmethod
    def get_id() -> str:
        """Return service id."""
        return "nextcloud"

    @staticmethod
    def get_display_name(locale: str = "en") -> str:
        """Return service display name."""
        return L10n().get("services.nextcloud.display_name", locale)

    @staticmethod
    def get_description(locale: str = "en") -> str:
        """Return service description."""
        return L10n().get("services.nextcloud.description", locale)

    @staticmethod
    def get_svg_icon() -> str:
        """Read SVG icon from file and return it as base64 encoded string."""
        return base64.b64encode(NEXTCLOUD_ICON.encode("utf-8")).decode("utf-8")

    @staticmethod
    def get_url() -> typing.Optional[str]:
        """Return service url."""
        domain = get_domain()
        return f"https://cloud.{domain}"

    @staticmethod
    def is_movable() -> bool:
        return True

    @staticmethod
    def is_required() -> bool:
        return False

    @staticmethod
    def is_enabled() -> bool:
        with ReadUserData() as user_data:
            return user_data.get("nextcloud", {}).get("enable", False)

    @staticmethod
    def get_status() -> ServiceStatus:
        """
        Return Nextcloud status from systemd.
        Use command return code to determine status.

        Return code 0 means service is running.
        Return code 1 or 2 means service is in error stat.
        Return code 3 means service is stopped.
        Return code 4 means service is off.
        """
        return get_service_status("phpfpm-nextcloud.service")

    @staticmethod
    def enable():
        """Enable Nextcloud service."""
        with WriteUserData() as user_data:
            if "nextcloud" not in user_data:
                user_data["nextcloud"] = {}
            user_data["nextcloud"]["enable"] = True

    @staticmethod
    def disable():
        """Disable Nextcloud service."""
        with WriteUserData() as user_data:
            if "nextcloud" not in user_data:
                user_data["nextcloud"] = {}
            user_data["nextcloud"]["enable"] = False

    @staticmethod
    def stop():
        """Stop Nextcloud service."""
        subprocess.Popen(["systemctl", "stop", "phpfpm-nextcloud.service"])

    @staticmethod
    def start():
        """Start Nextcloud service."""
        subprocess.Popen(["systemctl", "start", "phpfpm-nextcloud.service"])

    @staticmethod
    def restart():
        """Restart Nextcloud service."""
        subprocess.Popen(["systemctl", "restart", "phpfpm-nextcloud.service"])

    @staticmethod
    def get_configuration() -> dict:
        """Return Nextcloud configuration."""
        return {}

    @staticmethod
    def set_configuration(config_items):
        return super().set_configuration(config_items)

    @staticmethod
    def get_logs():
        """Return Nextcloud logs."""
        return ""

    @staticmethod
    def get_storage_usage() -> int:
        """
        Calculate the real storage usage of /var/lib/nextcloud and all subdirectories.
        Calculate using pathlib.
        Do not follow symlinks.
        """
        return get_storage_usage("/var/lib/nextcloud")

    @staticmethod
    def get_location() -> str:
        """Get the name of disk where Nextcloud is installed."""
        with ReadUserData() as user_data:
            if user_data.get("useBinds", False):
                return user_data.get("nextcloud", {}).get("location", "sda1")
            else:
                return "sda1"

    @staticmethod
    def get_dns_records() -> typing.List[ServiceDnsRecord]:
        return [
            ServiceDnsRecord(
                type="A",
                name="cloud",
                content=network_utils.get_ip4(),
                ttl=3600,
            ),
            ServiceDnsRecord(
                type="AAAA",
                name="cloud",
                content=network_utils.get_ip6(),
                ttl=3600,
            ),
        ]

    def move_to_volume(self, volume: BlockDevice, locale: str = "en") -> Job:
        job = Jobs.add(
            type_id="services.nextcloud.move",
            name=L10n().get("services.nextcloud.move_job.name", locale),
            description=L10n()
            .get("services.nextcloud.move_job.description", locale)
            .format(volume=volume.name),
        )
        move_service(
            self,
            volume,
            job,
            [
                FolderMoveNames(
                    name="nextcloud",
                    bind_location="/var/lib/nextcloud",
                    owner="nextcloud",
                    group="nextcloud",
                ),
            ],
            "nextcloud",
        )
        return job
