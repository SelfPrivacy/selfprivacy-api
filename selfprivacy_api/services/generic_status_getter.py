"""Generic service status fetcher using systemctl"""
import subprocess

from selfprivacy_api.services.service import ServiceStatus


def get_service_status(service: str) -> ServiceStatus:
    """
    Return service status from systemd.
    Use systemctl show to get the status of a service.
    Get ActiveState from the output.
    """
    service_status = subprocess.check_output(["systemctl", "show", service])
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
