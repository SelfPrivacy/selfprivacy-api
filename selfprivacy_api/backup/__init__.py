from typing import List

from selfprivacy_api.models.backup.snapshot import Snapshot

from selfprivacy_api.utils.singleton_metaclass import SingletonMetaclass

from selfprivacy_api.services.service import Service
from selfprivacy_api.backup.providers.provider import AbstractBackupProvider
from selfprivacy_api.backup.providers import get_provider
from selfprivacy_api.graphql.queries.providers import BackupProvider


class Backups(metaclass=SingletonMetaclass):
    """A singleton controller for backups"""

    provider: AbstractBackupProvider

    def __init__(self):
        self.lookup_provider()

    def lookup_provider(self):
        redis_provider = Backups.load_provider_redis()
        if redis_provider is not None:
            self.provider = redis_provider

        json_provider = Backups.load_provider_json()
        if json_provider is not None:
            self.provider = json_provider

        provider_class = get_provider(BackupProvider.MEMORY)
        self.provider = provider_class(login="", key="")

    @staticmethod
    def load_provider_redis() -> AbstractBackupProvider:
        pass

    @staticmethod
    def load_provider_json() -> AbstractBackupProvider:
        pass

    def back_up(self, service: Service):
        folder = service.get_location()
        repo_name = service.get_id()

        service.pre_backup()
        self.provider.backuper.start_backup(folder, repo_name)
        service.post_restore()

    def get_snapshots(self, service: Service) -> List[Snapshot]:
        repo_name = service.get_id()

        return self.provider.backuper.get_snapshots(repo_name)
