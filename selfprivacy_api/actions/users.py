"""Actions to manage the users."""

import re
from typing import Optional

from selfprivacy_api.models.user import UserDataUser

from selfprivacy_api.utils import is_username_forbidden

from selfprivacy_api.repositories.users.json_user_repository import JsonUserRepository
from selfprivacy_api.repositories.users import ACTIVE_USERS_PROVIDER
from selfprivacy_api.repositories.users.exceptions import (
    UsernameForbidden,
    UsernameNotAlphanumeric,
    UsernameTooLong,
)


def get_users(
    exclude_primary: bool = False,
    exclude_root: bool = False,
) -> list[UserDataUser]:
    users = ACTIVE_USERS_PROVIDER.get_users(
        exclude_primary=exclude_primary, exclude_root=exclude_root
    )

    # for user in users:
    # TODO: take ssh keys if ACTIVE_USERS_PROVIDER is KanidmUserRepository
    return users


def create_user(
    username: str,
    password: Optional[str] = None,
    displayname: Optional[str] = None,
    email: Optional[str] = None,
    directmemberof: Optional[list[str]] = None,
    memberof: Optional[list[str]] = None,
) -> None:

    if is_username_forbidden(username):
        raise UsernameForbidden("Username is forbidden")

    if not re.match(r"^[a-z_][a-z0-9_]+$", username):
        raise UsernameNotAlphanumeric(
            "Username must be alphanumeric and start with a letter"
        )

    if len(username) >= 32:
        raise UsernameTooLong("Username must be less than 32 characters")

    if ACTIVE_USERS_PROVIDER != JsonUserRepository:  # for ssh management
        JsonUserRepository.create_user(username=username, password="legacy")

    return ACTIVE_USERS_PROVIDER.create_user(
        username=username,
        password=password,
        displayname=displayname,
        email=email,
        directmemberof=directmemberof,
        memberof=memberof,
    )


def delete_user(username: str) -> None:
    if ACTIVE_USERS_PROVIDER != JsonUserRepository:  # for ssh management
        JsonUserRepository.delete_user(username=username)

    return ACTIVE_USERS_PROVIDER.delete_user(username=username)


def update_user(
    username: str,
    password: Optional[str] = None,
    displayname: Optional[str] = None,
    email: Optional[str] = None,
    directmemberof: Optional[list[str]] = None,
    memberof: Optional[list[str]] = None,
) -> None:

    return ACTIVE_USERS_PROVIDER.update_user(
        username=username,
        password=password,
        displayname=displayname,
        email=email,
        directmemberof=directmemberof,
        memberof=memberof,
    )


def get_user_by_username(username: str) -> Optional[UserDataUser]:
    user = ACTIVE_USERS_PROVIDER.get_user_by_username(username=username)

    # TODO: take ssh keys if ACTIVE_USERS_PROVIDER is KanidmUserRepository
    return user
