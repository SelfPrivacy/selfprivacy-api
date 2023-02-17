"""Handling of local secret used for encrypted backups.
Separated out for circular dependency reasons
"""

REDIS_KEY = "backup:local_secret"


class LocalBackupSecret:
    @staticmethod
    def get():
        """A secret string which backblaze/other clouds do not know.
        Serves as encryption key.
        TODO: generate and save in redis
        """
        return "TEMPORARY_SECRET"

    @staticmethod
    def reset():
        pass

    def exists():
        pass

    @staticmethod
    def _generate():
        pass

    @staticmethod
    def _store(secret: str):
        pass
