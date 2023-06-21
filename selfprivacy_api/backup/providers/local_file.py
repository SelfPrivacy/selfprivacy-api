from .provider import AbstractBackupProvider
from selfprivacy_api.backup.backuppers.restic_backupper import ResticBackuper


class LocalFileBackup(AbstractBackupProvider):
    backuper = ResticBackuper("", "", ":local:")
    name = "FILE"
