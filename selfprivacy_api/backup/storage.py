from typing import List, Optional
from datetime import datetime

from selfprivacy_api.models.backup.snapshot import Snapshot
from selfprivacy_api.models.backup.provider import BackupProviderModel

from selfprivacy_api.utils.redis_pool import RedisPool
from selfprivacy_api.utils.redis_model_storage import store_model_as_hash, hash_as_model


from selfprivacy_api.services.service import Service

from selfprivacy_api.backup.providers.provider import AbstractBackupProvider
from selfprivacy_api.backup.providers import get_kind

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


class Storage:
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
    def invalidate_snapshot_storage():
        for key in redis.keys(REDIS_SNAPSHOTS_PREFIX + "*"):
            redis.delete(key)

    @staticmethod
    def store_testrepo_path(path: str):
        redis.set(REDIS_REPO_PATH_KEY, path)

    @staticmethod
    def get_testrepo_path() -> str:
        if not redis.exists(REDIS_REPO_PATH_KEY):
            raise ValueError(
                "No test repository filepath is set, but we tried to access it"
            )
        return redis.get(REDIS_REPO_PATH_KEY)

    @staticmethod
    def services_with_autobackup() -> List[str]:
        keys = redis.keys(REDIS_AUTOBACKUP_ENABLED_PREFIX + "*")
        service_ids = [key.split(":")[-1] for key in keys]
        return service_ids

    @staticmethod
    def __last_backup_key(service_id):
        return REDIS_LAST_BACKUP_PREFIX + service_id

    @staticmethod
    def __snapshot_key(snapshot: Snapshot):
        return REDIS_SNAPSHOTS_PREFIX + snapshot.id

    @staticmethod
    def get_last_backup_time(service_id: str) -> Optional[datetime]:
        key = Storage.__last_backup_key(service_id)
        if not redis.exists(key):
            return None

        snapshot = hash_as_model(redis, key, Snapshot)
        return snapshot.created_at

    @staticmethod
    def store_last_timestamp(service_id: str, snapshot: Snapshot):
        store_model_as_hash(redis, Storage.__last_backup_key(service_id), snapshot)

    @staticmethod
    def cache_snapshot(snapshot: Snapshot):
        snapshot_key = Storage.__snapshot_key(snapshot)
        store_model_as_hash(redis, snapshot_key, snapshot)
        redis.expire(snapshot_key, REDIS_SNAPSHOT_CACHE_EXPIRE_SECONDS)

    @staticmethod
    def delete_cached_snapshot(snapshot: Snapshot):
        snapshot_key = Storage.__snapshot_key(snapshot)
        redis.delete(snapshot_key)

    @staticmethod
    def get_cached_snapshot_by_id(snapshot_id: str) -> Optional[Snapshot]:
        key = redis.keys(REDIS_SNAPSHOTS_PREFIX + snapshot_id)
        if not redis.exists(key):
            return None
        return hash_as_model(redis, key, Snapshot)

    @staticmethod
    def get_cached_snapshots() -> List[Snapshot]:
        keys = redis.keys(REDIS_SNAPSHOTS_PREFIX + "*")
        result = []

        for key in keys:
            snapshot = hash_as_model(redis, key, Snapshot)
            result.append(snapshot)
        return result

    @staticmethod
    def __autobackup_key(service_name: str) -> str:
        return REDIS_AUTOBACKUP_ENABLED_PREFIX + service_name

    @staticmethod
    def set_autobackup(service: Service):
        # shortcut this
        redis.set(Storage.__autobackup_key(service.get_id()), 1)

    @staticmethod
    def unset_autobackup(service: Service):
        """also see disable_all_autobackup()"""
        redis.delete(Storage.__autobackup_key(service.get_id()))

    @staticmethod
    def is_autobackup_set(service_name: str) -> bool:
        return redis.exists(Storage.__autobackup_key(service_name))

    @staticmethod
    def autobackup_period_minutes() -> Optional[int]:
        """None means autobackup is disabled"""
        if not redis.exists(REDIS_AUTOBACKUP_PERIOD_KEY):
            return None
        return int(redis.get(REDIS_AUTOBACKUP_PERIOD_KEY))

    @staticmethod
    def store_autobackup_period_minutes(minutes: int):
        redis.set(REDIS_AUTOBACKUP_PERIOD_KEY, minutes)

    @staticmethod
    def delete_backup_period():
        redis.delete(REDIS_AUTOBACKUP_PERIOD_KEY)

    @staticmethod
    def store_provider(provider: AbstractBackupProvider):
        store_model_as_hash(
            redis,
            REDIS_PROVIDER_KEY,
            BackupProviderModel(
                kind=get_kind(provider),
                login=provider.login,
                key=provider.key,
                location=provider.location,
                repo_id=provider.repo_id,
            ),
        )

    @staticmethod
    def load_provider() -> BackupProviderModel:
        provider_model = hash_as_model(redis, REDIS_PROVIDER_KEY, BackupProviderModel)
        return provider_model

    @staticmethod
    def has_init_mark() -> bool:
        if redis.exists(REDIS_INITTED_CACHE_PREFIX):
            return True
        return False

    @staticmethod
    def mark_as_init():
        redis.set(REDIS_INITTED_CACHE_PREFIX, 1)
