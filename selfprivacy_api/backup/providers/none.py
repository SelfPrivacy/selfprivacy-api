from .provider import AbstractBackupProvider
from selfprivacy_api.backup.backuppers.none_backupper import NoneBackupper
from selfprivacy_api.graphql.queries.providers import (
    BackupProvider as BackupProviderEnum,
)


class NoBackups(AbstractBackupProvider):
    @property
    def backuper(self):
        return NoneBackupper()

    name = BackupProviderEnum.NONE
