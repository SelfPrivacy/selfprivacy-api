from typing import List

from selfprivacy_api.models.backup.snapshot import Snapshot
from selfprivacy_api.models.backup.provider import BackupProviderModel

from selfprivacy_api.utils.singleton_metaclass import SingletonMetaclass
from selfprivacy_api.utils import ReadUserData
from selfprivacy_api.utils.redis_pool import RedisPool
from selfprivacy_api.utils.redis_model_storage import store_model_as_hash, hash_as_model


from selfprivacy_api.services import get_service_by_id
from selfprivacy_api.services.service import Service

from selfprivacy_api.backup.providers.provider import AbstractBackupProvider
from selfprivacy_api.backup.providers import get_provider, get_kind
from selfprivacy_api.graphql.queries.providers import BackupProvider

REDIS_PROVIDER_KEY = "backups:provider"
REDIS_INITTED_CACHE_PREFIX = "backups:initted_services:"

redis = RedisPool().get_connection()


# Singleton has a property of being persistent between tests.
# I don't know what to do with this yet
# class Backups(metaclass=SingletonMetaclass):
class Backups:
    """A singleton controller for backups"""

    provider: AbstractBackupProvider

    def __init__(self, test_repo_file: str = ""):
        if test_repo_file != "":
            self.set_localfile_repo(test_repo_file)
        else:
            self.provider = self.lookup_provider()

    def set_localfile_repo(self, file_path: str):
        ProviderClass = get_provider(BackupProvider.FILE)
        provider = ProviderClass(file_path)
        self.provider = provider

    @staticmethod
    def construct_provider(kind: str, login: str, key: str):
        provider_class = get_provider(BackupProvider[kind])
        return provider_class(login=login, key=key)

    @staticmethod
    def store_provider_redis(provider: AbstractBackupProvider):
        store_model_as_hash(
            redis,
            REDIS_PROVIDER_KEY,
            BackupProviderModel(
                kind=get_kind(provider), login=provider.login, key=provider.key
            ),
        )

    @staticmethod
    def load_provider_redis() -> AbstractBackupProvider:
        provider_model = hash_as_model(redis, REDIS_PROVIDER_KEY, BackupProviderModel)
        if provider_model is None:
            return None
        return Backups.construct_provider(
            provider_model.kind, provider_model.login, provider_model.key
        )

    @staticmethod
    def reset():
        redis.delete(REDIS_PROVIDER_KEY)
        for key in redis.keys(REDIS_INITTED_CACHE_PREFIX + "*"):
            redis.delete(key)

    def lookup_provider(self) -> AbstractBackupProvider:
        redis_provider = Backups.load_provider_redis()
        if redis_provider is not None:
            return redis_provider

        json_provider = Backups.load_provider_json()
        if json_provider is not None:
            return json_provider

        return Backups.construct_provider("MEMORY", login="", key="")

    @staticmethod
    def load_provider_json() -> AbstractBackupProvider:
        with ReadUserData() as user_data:
            account = ""
            key = ""

            if "backup" not in user_data.keys():
                if "backblaze" in user_data.keys():
                    account = user_data["backblaze"]["accountId"]
                    key = user_data["backblaze"]["accountKey"]
                    provider_string = "BACKBLAZE"
                    return Backups.construct_provider(
                        kind=provider_string, login=account, key=key
                    )
                return None

            account = user_data["backup"]["accountId"]
            key = user_data["backup"]["accountKey"]
            provider_string = user_data["backup"]["provider"]
            return Backups.construct_provider(
                kind=provider_string, login=account, key=key
            )

    def back_up(self, service: Service):
        folder = service.get_location()
        repo_name = service.get_id()

        service.pre_backup()
        self.provider.backuper.start_backup(folder, repo_name)
        service.post_restore()

    def init_repo(self, service: Service):
        repo_name = service.get_id()
        self.provider.backuper.init(repo_name)
        self._redis_mark_as_init(service)

    def _has_redis_init_mark(self, service: Service) -> bool:
        repo_name = service.get_id()
        if redis.exists(REDIS_INITTED_CACHE_PREFIX + repo_name):
            return True
        return False

    def _redis_mark_as_init(self, service: Service):
        repo_name = service.get_id()
        redis.set(REDIS_INITTED_CACHE_PREFIX + repo_name, 1)

    def is_initted(self, service: Service) -> bool:
        repo_name = service.get_id()
        if self._has_redis_init_mark(service):
            return True

        initted = self.provider.backuper.is_initted(repo_name)
        if initted:
            self._redis_mark_as_init(service)
            return True

        return False

    def get_snapshots(self, service: Service) -> List[Snapshot]:
        repo_name = service.get_id()

        return self.provider.backuper.get_snapshots(repo_name)

    def restore_service_from_snapshot(self, service: Service, snapshot_id: str):
        repo_name = service.get_id()
        folder = service.get_location()

        self.provider.backuper.restore_from_backup(repo_name, snapshot_id, folder)

    # Our dummy service is not yet globally registered so this is not testable yet
    def restore_snapshot(self, snapshot: Snapshot):
        self.restore_service_from_snapshot(
            get_service_by_id(snapshot.service_name), snapshot.id
        )

    def service_snapshot_size(self, service: Service, snapshot_id: str) -> float:
        repo_name = service.get_id()
        return self.provider.backuper.restored_size(repo_name, snapshot_id)

    # Our dummy service is not yet globally registered so this is not testable yet
    def snapshot_restored_size(self, snapshot: Snapshot) -> float:
        return self.service_snapshot_size(
            get_service_by_id(snapshot.service_name), snapshot.id
        )
