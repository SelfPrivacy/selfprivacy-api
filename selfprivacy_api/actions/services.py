import gettext

from selfprivacy_api.utils.localization import TranslateSystemMessage as t
from selfprivacy_api.utils.block_devices import BlockDevices
from selfprivacy_api.jobs import Jobs, Job

from selfprivacy_api.services import ServiceManager
from selfprivacy_api.services.tasks import move_service as move_service_task

_ = gettext.gettext


class ServiceNotFoundError(Exception):
    def __init__(self, service_id: str):
        self.service_id = service_id

    def get_error_message(self, locale: str) -> str:
        return t.translate(text=_("No such service: %(service_id)s"), locale=locale) % {
            "service_id": self.service_id
        }


class VolumeNotFoundError(Exception):
    def __init__(self, volume_name: str):
        self.volume_name = volume_name

    def get_error_message(self, locale: str) -> str:
        return t.translate(text=_("No such volume: %(volume_name)s"), locale=locale) % {
            "volume_name": self.volume_name
        }


def move_service(service_id: str, volume_name: str) -> Job:
    service = ServiceManager.get_service_by_id(service_id)
    if service is None:
        raise ServiceNotFoundError(service_id=service_id)

    volume = BlockDevices().get_block_device_by_canonical_name(volume_name)
    if volume is None:
        raise VolumeNotFoundError(volume_name=volume_name)

    service.assert_can_move(volume)

    job = Jobs.add(
        type_id=f"services.{service.get_id()}.move",
        name=_("Move %(service)s") % {"service": service.get_display_name()},
        description=_("Moving %(service)s data to %(volume)s")
        % {
            "service": service.get_display_name(),
            "volume": volume.get_display_name().lower(),
        },
    )

    move_service_task(service, volume, job)
    return job
