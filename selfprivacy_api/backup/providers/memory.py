from .provider import AbstractBackupProvider
from selfprivacy_api.backup.backuppers.restic_backupper import ResticBackupper
from selfprivacy_api.graphql.queries.providers import (
    BackupProvider as BackupProviderEnum,
)


class InMemoryBackup(AbstractBackupProvider):
    backupper = ResticBackupper("", "", ":memory:")

    name = BackupProviderEnum.MEMORY
