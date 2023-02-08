from abc import ABC, abstractmethod


class Backups:
    """A singleton controller for backups"""


class AbstractBackuper(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def start_backup(self, folder: str):
        raise NotImplementedError
