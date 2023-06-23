from .provider import AbstractBackupProvider
from selfprivacy_api.backup.backuppers.restic_backupper import ResticBackuper
from selfprivacy_api.graphql.queries.providers import (
    BackupProvider as BackupProviderEnum,
)


class LocalFileBackup(AbstractBackupProvider):
    @property
    def backuper(self):
        return ResticBackuper("", "", ":local:")

    name = BackupProviderEnum.FILE
