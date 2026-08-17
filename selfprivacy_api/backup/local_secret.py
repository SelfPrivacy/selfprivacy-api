"""Handling of local secret used for encrypted backups.
Separated out for circular dependency reasons
"""

from __future__ import annotations
import os
import secrets
import tempfile

from selfprivacy_api.utils.redis_pool import RedisPool

REDIS_KEY = "backup:local_secret"
RESTIC_PASSWORD_FILE = "/run/selfprivacy-api/restic-password"

redis = RedisPool().get_connection()


class LocalBackupSecret:
    @staticmethod
    def get() -> str:
        """
        A secret string which backblaze/other clouds do not know.
        Serves as encryption key.
        """
        if not LocalBackupSecret.exists():
            LocalBackupSecret.reset()
        return redis.get(REDIS_KEY)  # type: ignore

    @staticmethod
    def set(secret: str):
        redis.set(REDIS_KEY, secret)

    @staticmethod
    def password_file() -> str:
        """Write the current secret to restic's root-only password file."""
        password_file_dir = os.path.dirname(RESTIC_PASSWORD_FILE)
        os.makedirs(password_file_dir, mode=0o700, exist_ok=True)
        file_descriptor, temporary_file = tempfile.mkstemp(dir=password_file_dir)
        try:
            with os.fdopen(file_descriptor, "w", encoding="utf-8") as secret_file:
                os.fchmod(secret_file.fileno(), 0o600)
                secret_file.write(LocalBackupSecret.get())
                secret_file.write("\n")
            os.replace(temporary_file, RESTIC_PASSWORD_FILE)
        finally:
            if os.path.exists(temporary_file):
                os.unlink(temporary_file)
        return RESTIC_PASSWORD_FILE

    @staticmethod
    def reset():
        new_secret = LocalBackupSecret._generate()
        LocalBackupSecret.set(new_secret)

    @staticmethod
    def _full_reset():
        redis.delete(REDIS_KEY)

    @staticmethod
    def exists() -> bool:
        return redis.exists(REDIS_KEY) == 1

    @staticmethod
    def _generate() -> str:
        return secrets.token_urlsafe(256)
