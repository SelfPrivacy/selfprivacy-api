"""Class representing Bitwarden service"""
import base64
import typing
import subprocess

from typing import List
from os import path

# from enum import Enum

from selfprivacy_api.jobs import Job, Jobs, JobStatus
from selfprivacy_api.services.service import Service, ServiceDnsRecord, ServiceStatus
from selfprivacy_api.utils.block_devices import BlockDevice
from selfprivacy_api.services.generic_service_mover import move_service, FolderMoveNames
import selfprivacy_api.utils.network as network_utils

from selfprivacy_api.services.test_service.icon import BITWARDEN_ICON

DEFAULT_DELAY = 0


class DummyService(Service):
    """A test service"""

    folders: List[str] = []
    startstop_delay = 0.0
    backuppable = True
    movable = True
    # if False, we try to actually move
    simulate_moving = True
    drive = "sda1"

    def __init_subclass__(cls, folders: List[str]):
        cls.folders = folders

    def __init__(self):
        super().__init__()
        with open(self.status_file(), "w") as file:
            file.write(ServiceStatus.ACTIVE.value)
        with open(self.enabled_file(), "w") as file:
            file.write("True")

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
        domain = "test.com"
        return f"https://password.{domain}"

    @classmethod
    def is_movable(cls) -> bool:
        return cls.movable

    @staticmethod
    def is_required() -> bool:
        return False

    @staticmethod
    def get_backup_description() -> str:
        return "How did we get here?"

    @classmethod
    def is_enabled(cls) -> bool:
        return cls.get_enabled()

    @classmethod
    def status_file(cls) -> str:
        dir = cls.folders[0]
        # we do not REALLY want to store our state in our declared folders
        return path.join(dir, "..", "service_status")

    @classmethod
    def enabled_file(cls) -> str:
        dir = cls.folders[0]
        return path.join(dir, "..", "service_enabled")

    @classmethod
    def get_enabled(cls) -> bool:
        with open(cls.enabled_file(), "r") as file:
            string = file.read().strip()
        if "True" in string:
            return True
        if "False" in string:
            return False
        raise ValueError("test service enabled/disabled status file got corrupted")

    @classmethod
    def set_enabled(cls, enabled: bool):
        with open(cls.enabled_file(), "w") as file:
            status_string = file.write(str(enabled))

    @classmethod
    def set_status(cls, status: ServiceStatus):
        with open(cls.status_file(), "w") as file:
            status_string = file.write(status.value)

    @classmethod
    def get_status(cls) -> ServiceStatus:
        with open(cls.status_file(), "r") as file:
            status_string = file.read().strip()
        return ServiceStatus[status_string]

    @classmethod
    def change_status_with_async_delay(
        cls, new_status: ServiceStatus, delay_sec: float
    ):
        """simulating a delay on systemd side"""
        status_file = cls.status_file()

        command = [
            "bash",
            "-c",
            f" sleep {delay_sec} && echo {new_status.value} > {status_file}",
        ]
        handle = subprocess.Popen(command)
        if delay_sec == 0:
            handle.communicate()

    @classmethod
    def set_backuppable(cls, new_value: bool) -> None:
        """For tests: because can_be_backed_up is static,
        we can only set it up dynamically for tests via a classmethod"""
        cls.backuppable = new_value

    @classmethod
    def set_movable(cls, new_value: bool) -> None:
        """For tests: because is_movale is static,
        we can only set it up dynamically for tests via a classmethod"""
        cls.movable = new_value

    @classmethod
    def can_be_backed_up(cls) -> bool:
        """`True` if the service can be backed up."""
        return cls.backuppable

    @classmethod
    def enable(cls):
        cls.set_enabled(True)

    @classmethod
    def disable(cls):
        cls.set_enabled(False)

    @classmethod
    def set_delay(cls, new_delay_sec: float) -> None:
        cls.startstop_delay = new_delay_sec

    @classmethod
    def set_drive(cls, new_drive: str) -> None:
        cls.drive = new_drive

    @classmethod
    def set_simulated_moves(cls, enabled: bool) -> None:
        """If True, this service will not actually call moving code
        when moved"""
        cls.simulate_moving = enabled

    @classmethod
    def stop(cls):
        # simulate a failing service unable to stop
        if not cls.get_status() == ServiceStatus.FAILED:
            cls.set_status(ServiceStatus.DEACTIVATING)
            cls.change_status_with_async_delay(
                ServiceStatus.INACTIVE, cls.startstop_delay
            )

    @classmethod
    def start(cls):
        cls.set_status(ServiceStatus.ACTIVATING)
        cls.change_status_with_async_delay(ServiceStatus.ACTIVE, cls.startstop_delay)

    @classmethod
    def restart(cls):
        cls.set_status(ServiceStatus.RELOADING)  # is a correct one?
        cls.change_status_with_async_delay(ServiceStatus.ACTIVE, cls.startstop_delay)

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

    @classmethod
    def get_drive(cls) -> str:
        return cls.drive

    @classmethod
    def get_folders(cls) -> List[str]:
        return cls.folders

    @staticmethod
    def get_dns_records() -> typing.List[ServiceDnsRecord]:
        """Return list of DNS records for Bitwarden service."""
        return [
            ServiceDnsRecord(
                type="A",
                name="password",
                content=network_utils.get_ip4(),
                ttl=3600,
                display_name="Test Service",
            ),
            ServiceDnsRecord(
                type="AAAA",
                name="password",
                content=network_utils.get_ip6(),
                ttl=3600,
                display_name="Test Service (IPv6)",
            ),
        ]

    def move_to_volume(self, volume: BlockDevice) -> Job:
        job = Jobs.add(
            type_id=f"services.{self.get_id()}.move",
            name=f"Move {self.get_display_name()}",
            description=f"Moving {self.get_display_name()} data to {volume.name}",
        )
        if self.simulate_moving is False:
            # completely generic code, TODO: make it the default impl.
            move_service(
                self,
                volume,
                job,
                FolderMoveNames.default_foldermoves(self),
                self.get_id(),
            )
        else:
            Jobs.update(job, status=JobStatus.FINISHED)

        self.set_drive(volume.name)
        return job
