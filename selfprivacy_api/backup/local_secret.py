"""Handling of local secret used for encrypted backups.
Separated out for circular dependency reasons
"""

from __future__ import annotations
import secrets

from selfprivacy_api.utils.redis_pool import RedisPool


REDIS_KEY = "backup:local_secret"

redis = RedisPool().get_connection()


class LocalBackupSecret:
    @staticmethod
    def get():
        """A secret string which backblaze/other clouds do not know.
        Serves as encryption key.
        """
        if not LocalBackupSecret.exists():
            LocalBackupSecret.reset()
        return redis.get(REDIS_KEY)

    @staticmethod
    def reset():
        new_secret = LocalBackupSecret._generate()
        LocalBackupSecret._store(new_secret)

    @staticmethod
    def exists() -> bool:
        return redis.exists(REDIS_KEY)

    @staticmethod
    def _generate() -> str:
        return secrets.token_urlsafe(256)

    @staticmethod
    def _store(secret: str):
        redis.set(REDIS_KEY, secret)
