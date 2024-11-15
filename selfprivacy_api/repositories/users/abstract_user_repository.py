from abc import ABC, abstractmethod
from typing import Optional

from selfprivacy_api.models.user import UserDataUser


class AbstractUserRepository(ABC):
    @staticmethod
    @abstractmethod
    def get_users(
        exclude_primary: bool = False,
        exclude_root: bool = False,
    ) -> list[UserDataUser]:
        """Retrieves a list of users with options to exclude specific user groups"""

    @staticmethod
    @abstractmethod
    def create_user(username: str, password: str) -> None:
        """Creates a new user"""

    @staticmethod
    @abstractmethod
    def delete_user(username: str) -> None:
        """Deletes an existing user"""

    @staticmethod
    @abstractmethod
    def update_user(username: str, password: str) -> None:
        """Updates the password of an existing user"""

    @staticmethod
    @abstractmethod
    def get_user_by_username(username: str) -> Optional[UserDataUser]:
        """Retrieves user data (UserDataUser) by username"""
