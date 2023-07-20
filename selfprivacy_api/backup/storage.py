"""
Module for storing backup related data in redis.
"""
from typing import List, Optional
from datetime import datetime

from selfprivacy_api.models.backup.snapshot import Snapshot
from selfprivacy_api.models.backup.provider import BackupProviderModel

from selfprivacy_api.utils.redis_pool import RedisPool
from selfprivacy_api.utils.redis_model_storage import (
    store_model_as_hash,
    hash_as_model,
)

from selfprivacy_api.backup.providers.provider import AbstractBackupProvider
from selfprivacy_api.backup.providers import get_kind

# a hack to store file path.
REDIS_SNAPSHOT_CACHE_EXPIRE_SECONDS = 24 * 60 * 60  # one day

REDIS_SNAPSHOTS_PREFIX = "backups:snapshots:"
REDIS_LAST_BACKUP_PREFIX = "backups:last-backed-up:"
REDIS_INITTED_CACHE_PREFIX = "backups:initted_services:"

REDIS_PROVIDER_KEY = "backups:provider"
REDIS_AUTOBACKUP_PERIOD_KEY = "backups:autobackup_period"


redis = RedisPool().get_connection()


class Storage:
    """Static class for storing backup related data in redis"""
    @staticmethod
    def reset() -> None:
        """Deletes all backup related data from redis"""
        redis.delete(REDIS_PROVIDER_KEY)
        redis.delete(REDIS_AUTOBACKUP_PERIOD_KEY)

        prefixes_to_clean = [
            REDIS_INITTED_CACHE_PREFIX,
            REDIS_SNAPSHOTS_PREFIX,
            REDIS_LAST_BACKUP_PREFIX,
        ]

        for prefix in prefixes_to_clean:
            for key in redis.keys(prefix + "*"):
                redis.delete(key)

    @staticmethod
    def invalidate_snapshot_storage() -> None:
        """Deletes all cached snapshots from redis"""
        for key in redis.keys(REDIS_SNAPSHOTS_PREFIX + "*"):
            redis.delete(key)

    @staticmethod
    def __last_backup_key(service_id: str) -> str:
        return REDIS_LAST_BACKUP_PREFIX + service_id

    @staticmethod
    def __snapshot_key(snapshot: Snapshot) -> str:
        return REDIS_SNAPSHOTS_PREFIX + snapshot.id

    @staticmethod
    def get_last_backup_time(service_id: str) -> Optional[datetime]:
        """Returns last backup time for a service or None if it was never backed up"""
        key = Storage.__last_backup_key(service_id)
        if not redis.exists(key):
            return None

        snapshot = hash_as_model(redis, key, Snapshot)
        if not snapshot:
            return None
        return snapshot.created_at

    @staticmethod
    def store_last_timestamp(service_id: str, snapshot: Snapshot) -> None:
        """Stores last backup time for a service"""
        store_model_as_hash(
            redis,
            Storage.__last_backup_key(service_id),
            snapshot,
        )

    @staticmethod
    def cache_snapshot(snapshot: Snapshot) -> None:
        """Stores snapshot metadata in redis for caching purposes"""
        snapshot_key = Storage.__snapshot_key(snapshot)
        store_model_as_hash(redis, snapshot_key, snapshot)
        redis.expire(snapshot_key, REDIS_SNAPSHOT_CACHE_EXPIRE_SECONDS)

    @staticmethod
    def delete_cached_snapshot(snapshot: Snapshot) -> None:
        """Deletes snapshot metadata from redis"""
        snapshot_key = Storage.__snapshot_key(snapshot)
        redis.delete(snapshot_key)

    @staticmethod
    def get_cached_snapshot_by_id(snapshot_id: str) -> Optional[Snapshot]:
        """Returns cached snapshot by id or None if it doesn't exist"""
        key = REDIS_SNAPSHOTS_PREFIX + snapshot_id
        if not redis.exists(key):
            return None
        return hash_as_model(redis, key, Snapshot)

    @staticmethod
    def get_cached_snapshots() -> List[Snapshot]:
        """Returns all cached snapshots stored in redis"""
        keys: list[str] = redis.keys(REDIS_SNAPSHOTS_PREFIX + "*")  # type: ignore
        result: list[Snapshot] = []

        for key in keys:
            snapshot = hash_as_model(redis, key, Snapshot)
            if snapshot:
                result.append(snapshot)
        return result

    @staticmethod
    def autobackup_period_minutes() -> Optional[int]:
        """None means autobackup is disabled"""
        if not redis.exists(REDIS_AUTOBACKUP_PERIOD_KEY):
            return None
        return int(redis.get(REDIS_AUTOBACKUP_PERIOD_KEY))  # type: ignore

    @staticmethod
    def store_autobackup_period_minutes(minutes: int) -> None:
        """Set the new autobackup period in minutes"""
        redis.set(REDIS_AUTOBACKUP_PERIOD_KEY, minutes)

    @staticmethod
    def delete_backup_period() -> None:
        """Set the autobackup period to none, effectively disabling autobackup"""
        redis.delete(REDIS_AUTOBACKUP_PERIOD_KEY)

    @staticmethod
    def store_provider(provider: AbstractBackupProvider) -> None:
        """Stores backup stroage provider auth data in redis"""
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
    def load_provider() -> Optional[BackupProviderModel]:
        """Loads backup storage provider auth data from redis"""
        provider_model = hash_as_model(
            redis,
            REDIS_PROVIDER_KEY,
            BackupProviderModel,
        )
        return provider_model

    @staticmethod
    def has_init_mark() -> bool:
        """Returns True if the repository was initialized"""
        if redis.exists(REDIS_INITTED_CACHE_PREFIX):
            return True
        return False

    @staticmethod
    def mark_as_init():
        """Marks the repository as initialized"""
        redis.set(REDIS_INITTED_CACHE_PREFIX, 1)
