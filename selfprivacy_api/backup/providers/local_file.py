from .provider import AbstractBackupProvider
from selfprivacy_api.backup.restic_backuper import ResticBackuper


class LocalFileBackup(AbstractBackupProvider):
    backuper = ResticBackuper("", "", "memory")

    def __init__(self, filename: str):
        self.backuper = ResticBackuper("", "", f":local:{filename}/")
