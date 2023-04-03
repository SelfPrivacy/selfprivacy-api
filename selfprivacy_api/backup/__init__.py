from typing import List, Optional
from datetime import datetime

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

# a hack to store file path.
REDIS_SNAPSHOT_CACHE_EXPIRE_SECONDS = 24 * 60 * 60  # one day

REDIS_SNAPSHOTS_PREFIX = "backups:snapshots:"
REDIS_LAST_BACKUP_PREFIX = "backups:last-backed-up:"
REDIS_REPO_PATH_KEY = "backups:test_repo_path"

REDIS_PROVIDER_KEY = "backups:provider"
REDIS_INITTED_CACHE_PREFIX = "backups:initted_services:"

redis = RedisPool().get_connection()


# Singleton has a property of being persistent between tests.
# I don't know what to do with this yet
# class Backups(metaclass=SingletonMetaclass):
class Backups:
    """A singleton controller for backups"""

    provider: AbstractBackupProvider

    @staticmethod
    def set_localfile_repo(file_path: str):
        ProviderClass = get_provider(BackupProvider.FILE)
        provider = ProviderClass(file_path)
        redis.set(REDIS_REPO_PATH_KEY, file_path)
        Backups.store_provider_redis(provider)

    @staticmethod
    def _redis_last_backup_key(service_id):
        return REDIS_LAST_BACKUP_PREFIX + service_id

    @staticmethod
    def _redis_snapshot_key(snapshot: Snapshot):
        return REDIS_SNAPSHOTS_PREFIX + snapshot.id

    @staticmethod
    def get_last_backed_up(service: Service) -> Optional[datetime]:
        return Backups._get_last_backup_time_redis(service.get_id())

    @staticmethod
    def _get_last_backup_time_redis(service_id: str) -> Optional[datetime]:
        key = Backups._redis_last_backup_key(service_id)
        if not redis.exists(key):
            return None

        snapshot = hash_as_model(redis, key)
        return snapshot.created_at

    @staticmethod
    def _store_last_snapshot(service_id: str, snapshot: Snapshot):
        store_model_as_hash(redis, Backups._redis_last_backup_key(service_id), snapshot)

        snapshot_key = Backups._redis_snapshot_key(snapshot)
        store_model_as_hash(redis, snapshot_key, snapshot)
        redis.expire(snapshot_key, REDIS_SNAPSHOT_CACHE_EXPIRE_SECONDS)

    @staticmethod
    def provider():
        return Backups.lookup_provider()

    @staticmethod
    def set_provider(kind: str, login: str, key: str):
        provider = Backups.construct_provider(kind, login, key)
        Backups.store_provider_redis(provider)

    @staticmethod
    def construct_provider(kind: str, login: str, key: str):
        provider_class = get_provider(BackupProvider[kind])

        if kind == "FILE":
            path = redis.get(REDIS_REPO_PATH_KEY)
            return provider_class(path)

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
        redis.delete(REDIS_REPO_PATH_KEY)

        for key in redis.keys(REDIS_INITTED_CACHE_PREFIX + "*"):
            redis.delete(key)

        for key in redis.keys(REDIS_SNAPSHOTS_PREFIX + "*"):
            redis.delete(key)

        for key in redis.keys(REDIS_LAST_BACKUP_PREFIX + "*"):
            redis.delete(key)

    @staticmethod
    def lookup_provider() -> AbstractBackupProvider:
        redis_provider = Backups.load_provider_redis()
        if redis_provider is not None:
            return redis_provider

        json_provider = Backups.load_provider_json()
        if json_provider is not None:
            Backups.store_provider_redis(json_provider)
            return json_provider

        memory_provider = Backups.construct_provider("MEMORY", login="", key="")
        Backups.store_provider_redis(memory_provider)
        return memory_provider

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

    @staticmethod
    def back_up(service: Service):
        folder = service.get_location()
        repo_name = service.get_id()

        service.pre_backup()
        snapshot = Backups.provider().backuper.start_backup(folder, repo_name)
        Backups._store_last_snapshot(repo_name, snapshot)

        service.post_restore()

    @staticmethod
    def init_repo(service: Service):
        repo_name = service.get_id()
        Backups.provider().backuper.init(repo_name)
        Backups._redis_mark_as_init(service)

    @staticmethod
    def _has_redis_init_mark(service: Service) -> bool:
        repo_name = service.get_id()
        if redis.exists(REDIS_INITTED_CACHE_PREFIX + repo_name):
            return True
        return False

    @staticmethod
    def _redis_mark_as_init(service: Service):
        repo_name = service.get_id()
        redis.set(REDIS_INITTED_CACHE_PREFIX + repo_name, 1)

    @staticmethod
    def is_initted(service: Service) -> bool:
        repo_name = service.get_id()
        if Backups._has_redis_init_mark(service):
            return True

        initted = Backups.provider().backuper.is_initted(repo_name)
        if initted:
            Backups._redis_mark_as_init(service)
            return True

        return False

    @staticmethod
    def get_snapshots(service: Service) -> List[Snapshot]:
        repo_name = service.get_id()

        return Backups.provider().backuper.get_snapshots(repo_name)

    @staticmethod
    def restore_service_from_snapshot(service: Service, snapshot_id: str):
        repo_name = service.get_id()
        folder = service.get_location()

        Backups.provider().backuper.restore_from_backup(repo_name, snapshot_id, folder)

    # Our dummy service is not yet globally registered so this is not testable yet
    @staticmethod
    def restore_snapshot(snapshot: Snapshot):
        Backups.restore_service_from_snapshot(
            get_service_by_id(snapshot.service_name), snapshot.id
        )

    @staticmethod
    def service_snapshot_size(service: Service, snapshot_id: str) -> float:
        repo_name = service.get_id()
        return Backups.provider().backuper.restored_size(repo_name, snapshot_id)

    # Our dummy service is not yet globally registered so this is not testable yet
    @staticmethod
    def snapshot_restored_size(snapshot: Snapshot) -> float:
        return self.service_snapshot_size(
            get_service_by_id(snapshot.service_name), snapshot.id
        )
