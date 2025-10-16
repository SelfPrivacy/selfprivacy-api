"""Generic service status fetcher using systemctl"""

import asyncio
import subprocess
from typing import List

from sdbus import DbusInterfaceCommonAsync, dbus_method_async, dbus_property_async, encode_object_path
from selfprivacy_api.models.services import ServiceStatus

class SystemdUnitInterface(
    DbusInterfaceCommonAsync,
    interface_name='org.freedesktop.systemd1.Unit',
):
    @dbus_property_async(
        property_signature='s',
    )
    def active_state(self) -> str:
        raise NotImplementedError

class SystemdManagerInterface(DbusInterfaceCommonAsync, interface_name="org.freedesktop.systemd1.Manager"):
    @dbus_method_async(
        input_signature='',
        result_signature=''
    )
    async def reboot(self):
        raise NotImplementedError
    
    @dbus_method_async(
        input_signature='s',
        result_signature='o',
    )
    async def get_unit(
        self,
        name: str,
    ) -> str:
        raise NotImplementedError
   
    @dbus_method_async(
        input_signature='ss',
        result_signature='o',
    )
    async def start_unit(
        self,
        name: str,
        mode: str,
    ) -> str:
        raise NotImplementedError
    
    @dbus_method_async(
        input_signature='ss',
        result_signature='o',
    )
    async def restart_unit(
        self,
        name: str,
        mode: str,
    ) -> str:
        raise NotImplementedError
    
    @dbus_method_async(
        input_signature='ss',
        result_signature='o',
    )
    async def stop_unit(
        self,
        name: str,
        mode: str,
    ) -> str:
        raise NotImplementedError

systemd_proxy = SystemdManagerInterface.new_proxy(
    service_name="org.freedesktop.systemd1",
    object_path="/org/freedesktop/systemd1"
)

def get_unit_proxy(unit: str) -> SystemdUnitInterface:
    return SystemdUnitInterface.new_proxy(
        service_name='org.freedesktop.systemd1',
        object_path=encode_object_path('/org/freedesktop/systemd1/unit', unit)
    )

async def listen_for_unit_state_changes(units: List[str]):
    iterators = [get_unit_proxy(unit).properties_changed.__aiter__() for unit in units]
    pending: dict[int, asyncio.Task] = {}

    for i, it in enumerate(iterators):
        pending[i] = asyncio.create_task(it.__anext__())

    while pending:
        done, _ = await asyncio.wait(pending.values(), return_when=asyncio.FIRST_COMPLETED)

        for task in done:
            for idx, t in list(pending.items()):
                if t is task:
                    try:
                        item = t.result()
                        yield item
                        pending[idx] = asyncio.create_task(iterators[idx].__anext__())
                    except StopAsyncIteration:
                        del pending[idx]

                    break
    
    

async def wait_for_unit_state(unit: str, states: List[ServiceStatus]):
    unit_proxy = get_unit_proxy(unit)

    current_state = ServiceStatus.from_systemd_status(await unit_proxy.active_state)
    
    if current_state in states:
        return

    async for _ in unit_proxy.properties_changed:
        current_state = ServiceStatus.from_systemd_status(await unit_proxy.active_state)
        if current_state in states:
            return

async def start_unit(unit: str):
    await systemd_proxy.start_unit(unit, "replace")

async def stop_unit(unit: str):
    await systemd_proxy.stop_unit(unit, "replace")

async def restart_unit(unit: str):
    await systemd_proxy.restart_unit(unit, "replace")

async def get_service_status(unit: str) -> ServiceStatus:
    """
    Return service status from systemd.
    Use systemctl show to get the status of a service.
    Get ActiveState from the output.
    """
    try:
        unit_proxy = get_unit_proxy(unit)
        active_state: str = await unit_proxy.active_state
        return ServiceStatus.from_systemd_status(active_state)
    except Exception as e:
        print("DBUS ERROR", e)

    return ServiceStatus.OFF


async def get_service_status_from_several_units(services: list[str]) -> ServiceStatus:
    """
    Fetch all service statuses for all services and return the worst status.
    Statuses from worst to best:
    - OFF
    - FAILED
    - RELOADING
    - ACTIVATING
    - DEACTIVATING
    - INACTIVE
    - ACTIVE
    """
    service_statuses = []
    for service in services:
        service_statuses.append(await get_service_status(service))
    if ServiceStatus.OFF in service_statuses:
        return ServiceStatus.OFF
    if ServiceStatus.FAILED in service_statuses:
        return ServiceStatus.FAILED
    if ServiceStatus.RELOADING in service_statuses:
        return ServiceStatus.RELOADING
    if ServiceStatus.ACTIVATING in service_statuses:
        return ServiceStatus.ACTIVATING
    if ServiceStatus.DEACTIVATING in service_statuses:
        return ServiceStatus.DEACTIVATING
    if ServiceStatus.INACTIVE in service_statuses:
        return ServiceStatus.INACTIVE
    if ServiceStatus.ACTIVE in service_statuses:
        return ServiceStatus.ACTIVE
    return ServiceStatus.OFF


def get_last_log_lines(service: str, lines_count: int) -> List[str]:
    if lines_count < 1:
        raise ValueError("lines_count must be greater than 0")
    try:
        logs = subprocess.check_output(
            [
                "journalctl",
                "-u",
                service,
                "-n",
                str(lines_count),
                "-o",
                "cat",
            ],
            shell=False,
        ).decode("utf-8")
        return logs.splitlines()
    except subprocess.CalledProcessError:
        return []
