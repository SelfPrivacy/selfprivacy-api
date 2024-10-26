from typing import Optional

from selfprivacy_api.repositories.users.abstract_user_repository import (
    AbstractUserRepository,
    UserDataUser,
)

from selfprivacy_api.actions.users import (
    create_user,
    delete_user,
    get_user_by_username,
    get_users,
    update_user,
)


class JsonUserRepository(AbstractUserRepository):
    def get_users(
        exclude_primary: bool = False,
        exclude_root: bool = False,
    ) -> list[UserDataUser]:
        return get_users(exclude_primary=exclude_primary, exclude_root=exclude_root)

    def create_user(username: str, password: str):
        """Creates a new user"""
        return create_user(username=username, password=password)

    def delete_user(username: str) -> None:
        """Deletes an existing user"""
        return delete_user(username=username)

    def update_user(username: str, password: str) -> None:
        """Updates the password of an existing user"""
        return update_user(username=username, password=password)

    def get_user_by_username(username: str) -> Optional[UserDataUser]:
        """Retrieves user data (UserDataUser) by username"""
        return get_user_by_username(username=username)
