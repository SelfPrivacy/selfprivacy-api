from .provider import AbstractBackupProvider
from selfprivacy_api.backup.backuppers.restic_backupper import ResticBackuper
from selfprivacy_api.graphql.queries.providers import (
    BackupProvider as BackupProviderEnum,
)


class LocalFileBackup(AbstractBackupProvider):
    backuper = ResticBackuper("", "", ":local:")

    name = BackupProviderEnum.FILE
