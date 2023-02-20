from .provider import AbstractBackupProvider
from selfprivacy_api.backup.restic_backuper import ResticBackuper


class InMemoryBackup(AbstractBackupProvider):
    backuper = ResticBackuper("", "", ":memory:")
