"""Class representing Bitwarden service"""
import base64
import subprocess
import typing

from selfprivacy_api.jobs import Job, Jobs
from selfprivacy_api.services.generic_service_mover import FolderMoveNames, move_service
from selfprivacy_api.services.generic_status_getter import get_service_status
from selfprivacy_api.services.service import Service, ServiceDnsRecord, ServiceStatus
from selfprivacy_api.utils import ReadUserData, WriteUserData, get_domain
from selfprivacy_api.utils.block_devices import BlockDevice
from selfprivacy_api.utils.huey import huey
import selfprivacy_api.utils.network as network_utils
from selfprivacy_api.services.gitea.icon import GITEA_ICON


class Gitea(Service):
    """Class representing Gitea service"""

    @staticmethod
    def get_id() -> str:
        """Return service id."""
        return "gitea"

    @staticmethod
    def get_display_name() -> str:
        """Return service display name."""
        return "Gitea"

    @staticmethod
    def get_description() -> str:
        """Return service description."""
        return "Gitea is a Git forge."

    @staticmethod
    def get_svg_icon() -> str:
        """Read SVG icon from file and return it as base64 encoded string."""
        return base64.b64encode(GITEA_ICON.encode("utf-8")).decode("utf-8")

    @staticmethod
    def get_url() -> typing.Optional[str]:
        """Return service url."""
        domain = get_domain()
        return f"https://git.{domain}"

    @staticmethod
    def is_movable() -> bool:
        return True

    @staticmethod
    def is_required() -> bool:
        return False

    @staticmethod
    def is_enabled() -> bool:
        with ReadUserData() as user_data:
            return user_data.get("gitea", {}).get("enable", False)

    @staticmethod
    def get_status() -> ServiceStatus:
        """
        Return Gitea status from systemd.
        Use command return code to determine status.
        Return code 0 means service is running.
        Return code 1 or 2 means service is in error stat.
        Return code 3 means service is stopped.
        Return code 4 means service is off.
        """
        return get_service_status("gitea.service")

    @staticmethod
    def enable():
        """Enable Gitea service."""
        with WriteUserData() as user_data:
            if "gitea" not in user_data:
                user_data["gitea"] = {}
            user_data["gitea"]["enable"] = True

    @staticmethod
    def disable():
        """Disable Gitea service."""
        with WriteUserData() as user_data:
            if "gitea" not in user_data:
                user_data["gitea"] = {}
            user_data["gitea"]["enable"] = False

    @staticmethod
    def stop():
        subprocess.run(["systemctl", "stop", "gitea.service"])

    @staticmethod
    def start():
        subprocess.run(["systemctl", "start", "gitea.service"])

    @staticmethod
    def restart():
        subprocess.run(["systemctl", "restart", "gitea.service"])

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
    def get_folders() -> typing.List[str]:
        return ["/var/lib/gitea"]

    @staticmethod
    def get_drive() -> str:
        with ReadUserData() as user_data:
            if user_data.get("useBinds", False):
                return user_data.get("gitea", {}).get("location", "sda1")
            else:
                return "sda1"

    @staticmethod
    def get_dns_records() -> typing.List[ServiceDnsRecord]:
        return [
            ServiceDnsRecord(
                type="A",
                name="git",
                content=network_utils.get_ip4(),
                ttl=3600,
            ),
            ServiceDnsRecord(
                type="AAAA",
                name="git",
                content=network_utils.get_ip6(),
                ttl=3600,
            ),
        ]

    def move_to_volume(self, volume: BlockDevice) -> Job:
        job = Jobs.add(
            type_id="services.gitea.move",
            name="Move Gitea",
            description=f"Moving Gitea data to {volume.name}",
        )

        move_service(
            self,
            volume,
            job,
            FolderMoveNames.default_foldermoves(self),
            "gitea",
        )

        return job
