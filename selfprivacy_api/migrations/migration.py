from abc import ABC, abstractmethod


class Migration(ABC):
    """
    Abstract Migration class
    This class is used to define the structure of a migration
    Migration has a function is_migration_needed() that returns True or False
    Migration has a function migrate() that does the migration
    Migration has a function get_migration_name() that returns the migration name
    Migration has a function get_migration_description() that returns the migration description
    """

    @abstractmethod
    def get_migration_name(self) -> str:
        pass

    @abstractmethod
    def get_migration_description(self) -> str:
        pass

    @abstractmethod
    def is_migration_needed(self) -> bool:
        pass

    @abstractmethod
    def migrate(self) -> None:
        pass
