from abc import ABC, abstractmethod


class AbstractBackuper(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def start_backup(self, folder: str, repo_name: str):
        raise NotImplementedError
