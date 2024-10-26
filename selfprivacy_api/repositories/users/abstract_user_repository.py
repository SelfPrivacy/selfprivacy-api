from abc import ABC, abstractmethod
from typing import Optional

from pydantic import BaseModel
from enum import Enum


class UserDataUserOrigin(Enum):
    """Origin of the user in the user data"""

    NORMAL = "NORMAL"
    PRIMARY = "PRIMARY"
    ROOT = "ROOT"


class UserDataUser(BaseModel):
    """The user model from the userdata file"""

    username: str
    ssh_keys: list[str]
    origin: UserDataUserOrigin


class AbstractUserRepository(ABC):

    @abstractmethod
    def get_users(
        exclude_primary: bool = False,
        exclude_root: bool = False,
    ) -> list[UserDataUser]:
        """Retrieves a list of users with options to exclude specific user groups"""

    @abstractmethod
    def create_user(username: str, password: str):
        """Creates a new user"""

    @abstractmethod
    def delete_user(username: str) -> None:
        """Deletes an existing user"""

    @abstractmethod
    def update_user(username: str, password: str) -> None:
        """Updates the password of an existing user"""

    @abstractmethod
    def get_user_by_username(username: str) -> Optional[UserDataUser]:
        """Retrieves user data (UserDataUser) by username"""
