"""Generic service status fetcher using systemctl"""
import subprocess
import typing

from selfprivacy_api.services.service import ServiceStatus


def get_service_status(service: str) -> ServiceStatus:
    """
    Return service status from systemd.
    Use command return code to determine status.

    Return code 0 means service is running.
    Return code 1 or 2 means service is in error stat.
    Return code 3 means service is stopped.
    Return code 4 means service is off.
    """
    service_status = subprocess.Popen(["systemctl", "status", service])
    service_status.communicate()[0]
    if service_status.returncode == 0:
        return ServiceStatus.RUNNING
    elif service_status.returncode == 1 or service_status.returncode == 2:
        return ServiceStatus.ERROR
    elif service_status.returncode == 3:
        return ServiceStatus.STOPPED
    elif service_status.returncode == 4:
        return ServiceStatus.OFF
    else:
        return ServiceStatus.DEGRADED
