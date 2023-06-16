from .provider import AbstractBackupProvider
from selfprivacy_api.backup.backuppers.restic_backupper import ResticBackuper


class InMemoryBackup(AbstractBackupProvider):
    backuper = ResticBackuper("", "", ":memory:")

    name = "MEMORY"
