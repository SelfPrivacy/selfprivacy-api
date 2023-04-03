from typing import List, Optional
from datetime import datetime, timezone, timedelta

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

REDIS_AUTOBACKUP_ENABLED_PREFIX = "backup:autobackup:services:"
REDIS_SNAPSHOTS_PREFIX = "backups:snapshots:"
REDIS_LAST_BACKUP_PREFIX = "backups:last-backed-up:"
REDIS_INITTED_CACHE_PREFIX = "backups:initted_services:"

REDIS_REPO_PATH_KEY = "backups:test_repo_path"
REDIS_PROVIDER_KEY = "backups:provider"
REDIS_AUTOBACKUP_PERIOD_KEY = "backups:autobackup_period"


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
    def _redis_autobackup_key(service_name: str) -> str:
        return REDIS_AUTOBACKUP_ENABLED_PREFIX + service_name

    @staticmethod
    def enable_autobackup(service: Service):
        redis.set(Backups._redis_autobackup_key(service.get_id()), 1)

    @staticmethod
    def is_time_to_backup(time: datetime) -> bool:
        """
        Intended as a time validator for huey cron scheduler of automatic backups
        """
        for key in redis.keys(REDIS_AUTOBACKUP_ENABLED_PREFIX + "*"):
            service_id = key.split(":")[-1]
            if Backups.is_time_to_backup_service(service_id, time):
                return True
        return False

    @staticmethod
    def is_time_to_backup_service(service_id: str, time: datetime):
        period = Backups.autobackup_period_minutes()
        if period is None:
            return False
        if not Backups._is_autobackup_enabled_by_name(service_id) is None:
            return False

        last_backup = Backups._get_last_backup_time_redis(service_id)
        if last_backup is None:
            return True  # queue a backup immediately if there are no previous backups

        if time > last_backup + timedelta(minutes=period):
            return True
        return False

    @staticmethod
    def disable_autobackup(service: Service):
        """also see disable_all_autobackup()"""
        redis.delete(Backups._redis_autobackup_key(service.get_id()))

    @staticmethod
    def is_autobackup_enabled(service: Service) -> bool:
        return Backups._is_autobackup_enabled_by_name(service.get_id())

    @staticmethod
    def _is_autobackup_enabled_by_name(service_name: str):
        return redis.exists(Backups._redis_autobackup_key(service_name))

    @staticmethod
    def autobackup_period_minutes() -> Optional[int]:
        """None means autobackup is disabled"""
        if not redis.exists(REDIS_AUTOBACKUP_PERIOD_KEY):
            return None
        return int(redis.get(REDIS_AUTOBACKUP_PERIOD_KEY))

    @staticmethod
    def set_autobackup_period_minutes(minutes: int):
        """
        0 and negative numbers are equivalent to disable.
        Setting to a positive number may result in a backup very soon if some services are not backed up.
        """
        if minutes <= 0:
            Backups.disable_all_autobackup()
            return
        redis.set(REDIS_AUTOBACKUP_PERIOD_KEY, minutes)

    @staticmethod
    def disable_all_autobackup():
        """disables all automatic backing up, but does not change per-service settings"""
        redis.delete(REDIS_AUTOBACKUP_PERIOD_KEY)

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
        redis.delete(REDIS_AUTOBACKUP_PERIOD_KEY)

        prefixes_to_clean = [
            REDIS_INITTED_CACHE_PREFIX,
            REDIS_SNAPSHOTS_PREFIX,
            REDIS_LAST_BACKUP_PREFIX,
            REDIS_AUTOBACKUP_ENABLED_PREFIX,
        ]

        for prefix in prefixes_to_clean:
            for key in redis.keys(prefix + "*"):
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
        return Backups.service_snapshot_size(
            get_service_by_id(snapshot.service_name), snapshot.id
        )
