"""Abstract class for a service running on a server"""
from abc import ABC, abstractmethod
from enum import Enum
import typing

from pydantic import BaseModel
from selfprivacy_api.jobs import Job

from selfprivacy_api.utils.block_devices import BlockDevice

from selfprivacy_api.services.generic_size_counter import get_storage_usage


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
    priority: typing.Optional[int] = None


class Service(ABC):
    """
    Service here is some software that is hosted on the server and
    can be installed, configured and used by a user.
    """

    @staticmethod
    @abstractmethod
    def get_id() -> str:
        pass

    @staticmethod
    @abstractmethod
    def get_display_name() -> str:
        pass

    @staticmethod
    @abstractmethod
    def get_description() -> str:
        pass

    @staticmethod
    @abstractmethod
    def get_svg_icon() -> str:
        pass

    @staticmethod
    @abstractmethod
    def get_url() -> typing.Optional[str]:
        pass

    @classmethod
    def get_user(cls) -> typing.Optional[str]:
        return cls.get_id()

    @classmethod
    def get_group(cls) -> typing.Optional[str]:
        return cls.get_user()

    @staticmethod
    @abstractmethod
    def is_movable() -> bool:
        pass

    @staticmethod
    @abstractmethod
    def is_required() -> bool:
        pass

    @staticmethod
    @abstractmethod
    def is_enabled() -> bool:
        pass

    @staticmethod
    @abstractmethod
    def get_status() -> ServiceStatus:
        pass

    @staticmethod
    @abstractmethod
    def enable():
        pass

    @staticmethod
    @abstractmethod
    def disable():
        pass

    @staticmethod
    @abstractmethod
    def stop():
        pass

    @staticmethod
    @abstractmethod
    def start():
        pass

    @staticmethod
    @abstractmethod
    def restart():
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

    @staticmethod
    @abstractmethod
    def get_drive() -> str:
        pass

    @staticmethod
    @abstractmethod
    def get_folders() -> str:
        pass

    @staticmethod
    def get_foldername(path: str) -> str:
        return path.split("/")[-1]

    @abstractmethod
    def move_to_volume(self, volume: BlockDevice) -> Job:
        pass

    def pre_backup(self):
        pass

    def post_restore(self):
        pass
