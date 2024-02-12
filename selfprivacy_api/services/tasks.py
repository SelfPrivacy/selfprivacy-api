from selfprivacy_api.services import Service
from selfprivacy_api.utils.block_devices import BlockDevice
from selfprivacy_api.utils.huey import huey


@huey.task()
def move_service(
    service: Service,
    new_volume: BlockDevice,
):
    service.move_to_volume(new_volume)
