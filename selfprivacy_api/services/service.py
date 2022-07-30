"""Abstract class for a service running on a server"""
from abc import ABC, abstractmethod
from enum import Enum
import typing


class ServiceStatus(Enum):
    """Enum for service status"""

    RUNNING = "RUNNING"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"
    STOPPED = "STOPPED"
    OFF = "OFF"


class ServiceDnsRecord:
    type: str
    name: str
    content: str
    ttl: int
    priority: typing.Optional[int]


class Service(ABC):
    """
    Service here is some software that is hosted on the server and
    can be installed, configured and used by a user.
    """

    @abstractmethod
    def get_id(self) -> str:
        pass

    @abstractmethod
    def get_display_name(self) -> str:
        pass

    @abstractmethod
    def get_description(self) -> str:
        pass

    @abstractmethod
    def get_svg_icon(self) -> str:
        pass

    @abstractmethod
    def is_enabled(self) -> bool:
        pass

    @abstractmethod
    def get_status(self) -> ServiceStatus:
        pass

    @abstractmethod
    def enable(self):
        pass

    @abstractmethod
    def disable(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def restart(self):
        pass

    @abstractmethod
    def get_configuration(self):
        pass

    @abstractmethod
    def set_configuration(self, config_items):
        pass

    @abstractmethod
    def get_logs(self):
        pass

    @abstractmethod
    def get_storage_usage(self):
        pass

    @abstractmethod
    def get_dns_records(self) -> typing.List[ServiceDnsRecord]:
        pass
