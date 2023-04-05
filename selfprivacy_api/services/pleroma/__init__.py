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
import selfprivacy_api.utils.network as network_utils
from selfprivacy_api.services.pleroma.icon import PLEROMA_ICON


class Pleroma(Service):
    """Class representing Pleroma service."""

    @staticmethod
    def get_id() -> str:
        return "pleroma"

    @staticmethod
    def get_display_name() -> str:
        return "Pleroma"

    @staticmethod
    def get_description() -> str:
        return "Pleroma is a microblogging service that offers a web interface and a desktop client."

    @staticmethod
    def get_svg_icon() -> str:
        return base64.b64encode(PLEROMA_ICON.encode("utf-8")).decode("utf-8")

    @staticmethod
    def get_url() -> typing.Optional[str]:
        """Return service url."""
        domain = get_domain()
        return f"https://social.{domain}"

    @staticmethod
    def is_movable() -> bool:
        return True

    @staticmethod
    def is_required() -> bool:
        return False

    @staticmethod
    def is_enabled() -> bool:
        with ReadUserData() as user_data:
            return user_data.get("pleroma", {}).get("enable", False)

    @staticmethod
    def get_status() -> ServiceStatus:
        return get_service_status("pleroma.service")

    @staticmethod
    def enable():
        with WriteUserData() as user_data:
            if "pleroma" not in user_data:
                user_data["pleroma"] = {}
            user_data["pleroma"]["enable"] = True

    @staticmethod
    def disable():
        with WriteUserData() as user_data:
            if "pleroma" not in user_data:
                user_data["pleroma"] = {}
            user_data["pleroma"]["enable"] = False

    @staticmethod
    def stop():
        subprocess.run(["systemctl", "stop", "pleroma.service"])
        subprocess.run(["systemctl", "stop", "postgresql.service"])

    @staticmethod
    def start():
        subprocess.run(["systemctl", "start", "pleroma.service"])
        subprocess.run(["systemctl", "start", "postgresql.service"])

    @staticmethod
    def restart():
        subprocess.run(["systemctl", "restart", "pleroma.service"])
        subprocess.run(["systemctl", "restart", "postgresql.service"])

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
    def get_storage_usage() -> int:
        storage_usage = 0
        storage_usage += get_storage_usage("/var/lib/pleroma")
        storage_usage += get_storage_usage("/var/lib/postgresql")
        return storage_usage

    @staticmethod
    def get_location() -> str:
        with ReadUserData() as user_data:
            if user_data.get("useBinds", False):
                return user_data.get("pleroma", {}).get("location", "sda1")
            else:
                return "sda1"

    @staticmethod
    def get_dns_records() -> typing.List[ServiceDnsRecord]:
        return [
            ServiceDnsRecord(
                type="A",
                name="social",
                content=network_utils.get_ip4(),
                ttl=3600,
            ),
            ServiceDnsRecord(
                type="AAAA",
                name="social",
                content=network_utils.get_ip6(),
                ttl=3600,
            ),
        ]

    def move_to_volume(self, volume: BlockDevice) -> Job:
        job = Jobs.add(
            type_id="services.pleroma.move",
            name="Move Pleroma",
            description=f"Moving Pleroma to volume {volume.name}",
        )
        move_service(
            self,
            volume,
            job,
            [
                FolderMoveNames(
                    name="pleroma",
                    bind_location="/var/lib/pleroma",
                    owner="pleroma",
                    group="pleroma",
                ),
                FolderMoveNames(
                    name="postgresql",
                    bind_location="/var/lib/postgresql",
                    owner="postgres",
                    group="postgres",
                ),
            ],
            "pleroma",
        )
        return job
