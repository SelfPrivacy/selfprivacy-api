from .provider import AbstractBackupProvider
from selfprivacy_api.backup.restic_backuper import ResticBackuper


class LocalFileBackup(AbstractBackupProvider):
    backuper = ResticBackuper("", "", ":local:")
    name = "FILE"