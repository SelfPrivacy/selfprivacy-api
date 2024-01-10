"""Abstract class for a service running on a server"""
from abc import ABC, abstractmethod
from enum import Enum
import typing

from pydantic import BaseModel
from selfprivacy_api.jobs import Job

from selfprivacy_api.utils.block_devices import BlockDevice, BlockDevices

from selfprivacy_api.services.generic_size_counter import get_storage_usage
from selfprivacy_api.services.owned_path import OwnedPath
from selfprivacy_api import utils
from selfprivacy_api.utils.waitloop import wait_until_true
from selfprivacy_api.utils import ReadUserData, WriteUserData, get_domain

DEFAULT_START_STOP_TIMEOUT = 5 * 60


class ServiceStatus(Enum):
    """Enum for service status"""

    ACTIVE = "ACTIVE"
    RELOADING = "RELOADING"
    INACTIVE = "INACTIVE"
    FAILED = "FAILED"
    ACTIVATING = "ACTIVATING"
    DEACTIVATING = "DEACTIVATING"
    OFF = "OFF"


class ServiceDnsRecord(BaseModel):
    type: str
    name: str
    content: str
    ttl: int
    display_name: str
    priority: typing.Optional[int] = None


class Service(ABC):
    """
    Service here is some software that is hosted on the server and
    can be installed, configured and used by a user.
    """

    @staticmethod
    @abstractmethod
    def get_id() -> str:
        """
        The unique id of the service.
        """
        pass

    @staticmethod
    @abstractmethod
    def get_display_name() -> str:
        """
        The name of the service that is shown to the user.
        """
        pass

    @staticmethod
    @abstractmethod
    def get_description() -> str:
        """
        The description of the service that is shown to the user.
        """
        pass

    @staticmethod
    @abstractmethod
    def get_svg_icon() -> str:
        """
        The monochrome svg icon of the service.
        """
        pass

    @staticmethod
    @abstractmethod
    def get_url() -> typing.Optional[str]:
        """
        The url of the service if it is accessible from the internet browser.
        """
        pass

    @classmethod
    def get_user(cls) -> typing.Optional[str]:
        """
        The user that owns the service's files.
        Defaults to the service's id.
        """
        return cls.get_id()

    @classmethod
    def get_group(cls) -> typing.Optional[str]:
        """
        The group that owns the service's files.
        Defaults to the service's user.
        """
        return cls.get_user()

    @staticmethod
    @abstractmethod
    def is_movable() -> bool:
        """`True` if the service can be moved to the non-system volume."""
        pass

    @staticmethod
    @abstractmethod
    def is_required() -> bool:
        """`True` if the service is required for the server to function."""
        pass

    @staticmethod
    def can_be_backed_up() -> bool:
        """`True` if the service can be backed up."""
        return True

    @staticmethod
    @abstractmethod
    def get_backup_description() -> str:
        """
        The text shown to the user that exlplains what data will be
        backed up.
        """
        pass

    @classmethod
    def is_enabled(cls) -> bool:
        """
        `True` if the service is enabled.
        `False` if it is not enabled or not defined in file
        If there is nothing in the file, this is equivalent to False
        because NixOS won't enable it then.
        """
        name = cls.get_id()
        with ReadUserData() as user_data:
            return user_data.get("modules", {}).get(name, {}).get("enable", False)

    @staticmethod
    @abstractmethod
    def get_status() -> ServiceStatus:
        """The status of the service, reported by systemd."""
        pass

    @classmethod
    def _set_enable(cls, enable: bool):
        name = cls.get_id()
        with WriteUserData() as user_data:
            if "modules" not in user_data:
                user_data["modules"] = {}
            if name not in user_data["modules"]:
                user_data["modules"][name] = {}
            user_data["modules"][name]["enable"] = enable

    @classmethod
    def enable(cls):
        """Enable the service. Usually this means enabling systemd unit."""
        cls._set_enable(True)

    @classmethod
    def disable(cls):
        """Disable the service. Usually this means disabling systemd unit."""
        cls._set_enable(False)

    @staticmethod
    @abstractmethod
    def stop():
        """Stop the service. Usually this means stopping systemd unit."""
        pass

    @staticmethod
    @abstractmethod
    def start():
        """Start the service. Usually this means starting systemd unit."""
        pass

    @staticmethod
    @abstractmethod
    def restart():
        """Restart the service. Usually this means restarting systemd unit."""
        pass

    @staticmethod
    @abstractmethod
    def get_configuration():
        pass

    @staticmethod
    @abstractmethod
    def set_configuration(config_items):
        pass

    @staticmethod
    @abstractmethod
    def get_logs():
        pass

    @classmethod
    def get_storage_usage(cls) -> int:
        """
        Calculate the real storage usage of folders occupied by service
        Calculate using pathlib.
        Do not follow symlinks.
        """
        storage_used = 0
        for folder in cls.get_folders():
            storage_used += get_storage_usage(folder)
        return storage_used

    @staticmethod
    @abstractmethod
    def get_dns_records() -> typing.List[ServiceDnsRecord]:
        pass

    @classmethod
    def get_drive(cls) -> str:
        """
        Get the name of the drive/volume where the service is located.
        Example values are `sda1`, `vda`, `sdb`.
        """
        root_device: str = BlockDevices().get_root_block_device().name
        if not cls.is_movable():
            return root_device
        with utils.ReadUserData() as userdata:
            if userdata.get("useBinds", False):
                return (
                    userdata.get("modules", {})
                    .get(cls.get_id(), {})
                    .get(
                        "location",
                        root_device,
                    )
                )
            else:
                return root_device

    @classmethod
    def get_folders(cls) -> typing.List[str]:
        """
        get a plain list of occupied directories
        Default extracts info from overriden get_owned_folders()
        """
        if cls.get_owned_folders == Service.get_owned_folders:
            raise NotImplementedError(
                "you need to implement at least one of get_folders() or get_owned_folders()"
            )
        return [owned_folder.path for owned_folder in cls.get_owned_folders()]

    @classmethod
    def get_owned_folders(cls) -> typing.List[OwnedPath]:
        """
        Get a list of occupied directories with ownership info
        Default extracts info from overriden get_folders()
        """
        if cls.get_folders == Service.get_folders:
            raise NotImplementedError(
                "you need to implement at least one of get_folders() or get_owned_folders()"
            )
        return [cls.owned_path(path) for path in cls.get_folders()]

    @staticmethod
    def get_foldername(path: str) -> str:
        return path.split("/")[-1]

    @abstractmethod
    def move_to_volume(self, volume: BlockDevice) -> Job:
        """Cannot raise errors.
        Returns errors as an errored out Job instead."""
        pass

    @classmethod
    def owned_path(cls, path: str):
        """A default guess on folder ownership"""
        return OwnedPath(
            path=path,
            owner=cls.get_user(),
            group=cls.get_group(),
        )

    def pre_backup(self):
        pass

    def post_restore(self):
        pass


class StoppedService:
    """
    A context manager that stops the service if needed and reactivates it
    after you are done if it was active

    Example:
        ```
            assert service.get_status() == ServiceStatus.ACTIVE
            with StoppedService(service) [as stopped_service]:
                assert service.get_status() == ServiceStatus.INACTIVE
        ```
    """

    def __init__(self, service: Service):
        self.service = service
        self.original_status = service.get_status()

    def __enter__(self) -> Service:
        self.original_status = self.service.get_status()
        if self.original_status not in [ServiceStatus.INACTIVE, ServiceStatus.FAILED]:
            try:
                self.service.stop()
                wait_until_true(
                    lambda: self.service.get_status() == ServiceStatus.INACTIVE,
                    timeout_sec=DEFAULT_START_STOP_TIMEOUT,
                )
            except TimeoutError as error:
                raise TimeoutError(
                    f"timed out waiting for {self.service.get_display_name()} to stop"
                ) from error
        return self.service

    def __exit__(self, type, value, traceback):
        if self.original_status in [ServiceStatus.ACTIVATING, ServiceStatus.ACTIVE]:
            try:
                self.service.start()
                wait_until_true(
                    lambda: self.service.get_status() == ServiceStatus.ACTIVE,
                    timeout_sec=DEFAULT_START_STOP_TIMEOUT,
                )
            except TimeoutError as error:
                raise TimeoutError(
                    f"timed out waiting for {self.service.get_display_name()} to start"
                ) from error
