from abc import ABC, abstractmethod
from typing import Optional

from selfprivacy_api.models.user import UserDataUser


class AbstractUserRepository(ABC):
    @staticmethod
    @abstractmethod
    def create_user(
        username: str,
        password: Optional[str] = None,
        directmemberof: Optional[list[str]] = None,
        memberof: Optional[list[str]] = None,
        displayname: Optional[str] = None,
        email: Optional[str] = None,
    ) -> None:
        """
        Creates a new user. In KanidmUserRepository "password" is a legacy field,
        please use generate_password_reset_link() instead.
        """

    @staticmethod
    @abstractmethod
    def get_users(
        exclude_primary: bool = False,
        exclude_root: bool = False,
    ) -> list[UserDataUser]:
        """
        Gets a list of users with options to exclude specific user groups.
        In KanidmUserRepository, the root user will never return.
        """

    @staticmethod
    @abstractmethod
    def delete_user(username: str) -> None:
        """Deletes an existing user"""

    @staticmethod
    @abstractmethod
    def update_user(
        username: str,
        directmemberof: Optional[list[str]] = None,
        memberof: Optional[list[str]] = None,
        displayname: Optional[str] = None,
        email: Optional[str] = None,
    ) -> None:
        """
        Update user information.
        In the JsonUserRepository, only update the password of an existing user.
        Do not update the password in KanidmUserRepository,
        use generate_password_reset_link() instead.
        """

    @staticmethod
    @abstractmethod
    def get_user_by_username(username: str) -> UserDataUser:
        """Retrieves user data (UserDataUser) by username"""

    @staticmethod
    @abstractmethod
    def generate_password_reset_link(username: str) -> str:
        """
        Do not reset the password, just generate a link to reset the password.
        Not implemented in JsonUserRepository.
        """
