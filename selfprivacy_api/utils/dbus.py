import sdbus
from typing import Optional


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
