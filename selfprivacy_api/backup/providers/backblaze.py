from .provider import AbstractBackupProvider
from selfprivacy_api.backup.backuppers.restic_backupper import ResticBackuper
from selfprivacy_api.graphql.queries.providers import (
    BackupProvider as BackupProviderEnum,
)


class Backblaze(AbstractBackupProvider):
    @property
    def backuper(self):
        return ResticBackuper("--b2-account", "--b2-key", ":b2:")

    name = BackupProviderEnum.BACKBLAZE
