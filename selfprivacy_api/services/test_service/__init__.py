"""Class representing Bitwarden service"""

import base64
import asyncio

from selfprivacy_api.jobs import Job
from selfprivacy_api.services.service import Service, ServiceStatus
from selfprivacy_api.utils.block_devices import BlockDevice
from selfprivacy_api.utils.observable import Observable

from selfprivacy_api.services.test_service.icon import BITWARDEN_ICON


def async_deferred(fn):
    async def inner(*args, **kwargs):
        asyncio.create_task(fn(*args, **kwargs))

    return inner


def not_in_intermediate_state(state: ServiceStatus):
    return state not in [
        ServiceStatus.ACTIVATING,
        ServiceStatus.DEACTIVATING,
        ServiceStatus.RELOADING,
    ]


class DummyService(Service):
    """A test service"""

    folders: list[str] = []
    backuppable = True
    movable = True
    fail_on_stop = False
    # if False, we try to actually move
    simulate_moving = True
    drive = "sda1"

    state_observable = Observable(ServiceStatus.ACTIVE)

    def __init_subclass__(cls, folders: list[str]):
        cls.folders = folders

    def __init__(self):
        super().__init__()

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
    def get_svg_icon(raw=False) -> str:
        """Read SVG icon from file and return it as base64 encoded string."""
        if raw:
            return BITWARDEN_ICON
        return base64.b64encode(BITWARDEN_ICON.encode("utf-8")).decode("utf-8", "replace")

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
    async def set_status(cls, status: ServiceStatus):
        await cls.state_observable.put(status)

    @classmethod
    async def get_status(cls) -> ServiceStatus:
        return cls.state_observable.get()

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
    def set_drive(cls, new_drive: str) -> None:
        cls.drive = new_drive

    @classmethod
    def set_simulated_moves(cls, enabled: bool) -> None:
        """If True, this service will not actually call moving code
        when moved"""
        cls.simulate_moving = enabled

    @classmethod
    def simulate_fail_on_stop(cls, value: bool):
        cls.fail_on_stop = value

    @classmethod
    @async_deferred
    async def stop(cls):
        assert not_in_intermediate_state(await cls.get_status())

        await cls.set_status(ServiceStatus.DEACTIVATING)

        if cls.fail_on_stop:
            await cls.set_status(ServiceStatus.FAILED)
        else:
            await cls.set_status(ServiceStatus.INACTIVE)

    @classmethod
    @async_deferred
    async def start(cls):
        assert not_in_intermediate_state(await cls.get_status())

        await cls.set_status(ServiceStatus.ACTIVATING)
        await cls.set_status(ServiceStatus.ACTIVE)

    @classmethod
    @async_deferred
    async def restart(cls):
        assert not_in_intermediate_state(await cls.get_status())

        if await cls.get_status() is ServiceStatus.ACTIVE:
            await cls.set_status(ServiceStatus.DEACTIVATING)
            await cls.set_status(ServiceStatus.INACTIVE)

        await cls.set_status(ServiceStatus.ACTIVATING)
        await cls.set_status(ServiceStatus.ACTIVE)

    @classmethod
    def get_configuration(cls):
        return {}

    @classmethod
    def set_configuration(cls, config_items):
        return super().set_configuration(config_items)

    @staticmethod
    async def get_storage_usage() -> int:
        return 0

    @classmethod
    def get_drive(cls) -> str:
        return cls.drive

    @classmethod
    def get_folders(cls) -> list[str]:
        return cls.folders

    def do_move_to_volume(self, volume: BlockDevice, job: Job) -> Job:
        if self.simulate_moving is False:
            return super(DummyService, self).do_move_to_volume(volume, job)
        else:
            self.set_drive(volume.name)
            return job

    @classmethod
    async def wait_for_statuses(cls, expected_statuses: list[ServiceStatus]):
        async for state in cls.state_observable.subscribe():
            if state in expected_statuses:
                return
