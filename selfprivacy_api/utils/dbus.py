import sdbus
from collections.abc import Awaitable, Callable
from typing import Optional, TypeVar

from sdbus.exceptions import SdBusBaseError

from selfprivacy_api.exceptions.dbus import DbusCallFailed

T = TypeVar("T")


class DbusConnection:
    _instance: Optional["DbusConnection"] = None
    _bus: Optional[sdbus.SdBus] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # Only initialize once
        if self._bus is None:
            self._bus = sdbus.sd_bus_open_system()

    @property
    def bus(self) -> sdbus.SdBus:
        return self._bus

    @classmethod
    def get_instance(cls) -> "DbusConnection":
        """Get the singleton instance of DbusConnection."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


async def wrapped_dbus_call(call: Callable[[], Awaitable[T]], operation: str) -> T:
    try:
        return await call()
    except SdBusBaseError as error:
        raise DbusCallFailed(error=error, operation=operation) from error
