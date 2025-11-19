"""Class representing Bitwarden service"""

import base64
import asyncio

from selfprivacy_api.jobs import Job
from selfprivacy_api.services.service import Service, ServiceStatus
from selfprivacy_api.utils.block_devices import BlockDevice

from selfprivacy_api.services.test_service.icon import BITWARDEN_ICON

DEFAULT_DELAY = 0


class ServiceState:
    def __init__(self, queue: [ServiceStatus] = []):
        self._observers = []
        self.queue = queue
        self.state: ServiceStatus | None = None

    def change_state_from_queu(self):
        next_state = self.queue.pop(0)
        self.state = next_state
        self.notify(state=next_state)

    def change_state(self, new_state: ServiceStatus):
        self.state = new_state
        self.notify(state=new_state)

    def add_state_to_queue(self, state: ServiceStatus):
        self.queue.append(state)

    def attach(self, observer):
        self._observers.append(observer)

    def detach(self, observer):
        self._observers.remove(observer)

    def notify(self, state: ServiceStatus):
        for observer in self._observers:
            observer.update(state=state)


class Waiter:
    def __init__(self, service: ServiceState, desired: ServiceStatus):
        self.desired = desired
        self.future = asyncio.get_running_loop().create_future()

        service.attach(self)

        if service.state == desired:
            if not self.future.done():
                self.future.set_result(True)

    def update(self, state: ServiceStatus):
        if state == self.desired and not self.future.done():
            self.future.set_result(True)


class DummyService(Service):
    """A test service"""

    folders: list[str] = []
    startstop_delay = 0.0
    backuppable = True
    movable = True
    fail_to_stop = False
    # if False, we try to actually move
    simulate_moving = True
    drive = "sda1"

    state = ServiceState()

    def __init_subclass__(cls, folders: list[str]):
        cls.folders = folders

    def __init__(self):
        super().__init__()
        self.state.change_state(state=ServiceStatus.ACTIVE.value)

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
        # return ""
        if raw:
            return BITWARDEN_ICON
        return base64.b64encode(BITWARDEN_ICON.encode("utf-8")).decode("utf-8")

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
    def set_status(cls, status: ServiceStatus):
        cls.state.change_state = status

    @classmethod
    async def get_status(cls) -> ServiceStatus:
        if cls.state.state is None:
            raise ValueError("DummyService status is not initialized!")
        return cls.state.state

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
        """If True, th is service will not actually call moving code
        when moved"""
        cls.simulate_moving = enabled

    @classmethod
    def simulate_fail_to_stop(cls, value: bool):
        cls.fail_to_stop = value

    @classmethod
    async def stop(cls):
        # simulate a failing service unable to stop
        if not await cls.get_status() == ServiceStatus.FAILED:
            cls.set_status(ServiceStatus.DEACTIVATING)
            if cls.fail_to_stop:
                cls.set_status(ServiceStatus.FAILED)
            else:
                cls.set_status(ServiceStatus.INACTIVE)

    @classmethod
    async def start(cls):
        cls.set_status(ServiceStatus.ACTIVATING)
        cls.set_status(ServiceStatus.ACTIVE)

    @classmethod
    async def restart(cls):
        await cls.stop()
        await cls.start()

    @classmethod
    def get_configuration(cls):
        return {}

    @classmethod
    def set_configuration(cls, config_items):
        return super().set_configuration(config_items)

    @staticmethod
    async def get_storage_usage() -> int:
        storage_usage = 0
        return storage_usage

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
        if cls.state in expected_statuses:
            return

        waiters = [Waiter(cls.state, status) for status in expected_statuses]

        futures = [w.future for w in waiters]

        done, pending = await asyncio.wait(
            futures,
            return_when=asyncio.FIRST_COMPLETED,
        )

        for fut in pending:
            fut.cancel()

        return
