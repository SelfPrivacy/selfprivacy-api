from .provider import AbstractBackupProvider
from selfprivacy_api.backup.restic_backuper import ResticBackuper


class LocalFileBackup(AbstractBackupProvider):
    backuper = ResticBackuper("", "", "memory")

    # login and key args are for compatibility with generic provider methods. They are ignored.
    def __init__(self, filename: str, login: str = "", key: str = ""):
        super().__init__()
        self.backuper = ResticBackuper("", "", f":local:{filename}/")
