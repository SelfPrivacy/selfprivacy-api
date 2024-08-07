"""Generic service status fetcher using systemctl"""

import subprocess
from typing import List

from selfprivacy_api.models.services import ServiceStatus


def get_service_status(unit: str) -> ServiceStatus:
    """
    Return service status from systemd.
    Use systemctl show to get the status of a service.
    Get ActiveState from the output.
    """
    service_status = subprocess.check_output(["systemctl", "show", unit])
    if b"LoadState=not-found" in service_status:
        return ServiceStatus.OFF
    if b"ActiveState=active" in service_status:
        return ServiceStatus.ACTIVE
    if b"ActiveState=inactive" in service_status:
        return ServiceStatus.INACTIVE
    if b"ActiveState=activating" in service_status:
        return ServiceStatus.ACTIVATING
    if b"ActiveState=deactivating" in service_status:
        return ServiceStatus.DEACTIVATING
    if b"ActiveState=failed" in service_status:
        return ServiceStatus.FAILED
    if b"ActiveState=reloading" in service_status:
        return ServiceStatus.RELOADING
    return ServiceStatus.OFF


def get_service_status_from_several_units(services: list[str]) -> ServiceStatus:
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
        service_statuses.append(get_service_status(service))
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
