from selfprivacy_api.utils.huey import huey
from selfprivacy_api.services.service import Service
from selfprivacy_api.backup import Backups

# huey tasks need to return something
@huey.task()
def start_backup(service: Service) -> bool:
    Backups.back_up(service)
    return True
