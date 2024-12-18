"""Actions to manage the users."""

import re
import uuid
import logging
from typing import Optional

from selfprivacy_api.utils.strings import PLEASE_UPDATE_APP_TEXT
from selfprivacy_api.models.group import Group
from selfprivacy_api.models.user import UserDataUser, UserDataUserOrigin

from selfprivacy_api.utils import is_username_forbidden
from selfprivacy_api.actions.ssh import get_ssh_keys


from selfprivacy_api.repositories.users.json_user_repository import JsonUserRepository
from selfprivacy_api.repositories.users import ACTIVE_USERS_PROVIDER
from selfprivacy_api.repositories.users.exceptions import (
    DisplaynameTooLong,
    SelfPrivacyAppIsOutdate,
    UserIsProtected,
    UsernameForbidden,
    UsernameNotAlphanumeric,
    UsernameTooLong,
    UserNotFound,
    UserAlreadyExists,
    InvalidConfiguration,
)

logger = logging.getLogger(__name__)


class ApiUsingWrongUserRepository(Exception):
    """
    API is using a too old or unfinished user repository. Are you debugging?
    """

    @staticmethod
    def get_error_message() -> str:
        return "API is using a too old or unfinished user repository"


def get_users(
    exclude_primary: bool = False,
    exclude_root: bool = False,
) -> list[UserDataUser]:
    users = ACTIVE_USERS_PROVIDER.get_users(
        exclude_primary=exclude_primary, exclude_root=exclude_root
    )

    if isinstance(ACTIVE_USERS_PROVIDER, JsonUserRepository):
        for user in users:
            try:
                user.ssh_keys = get_ssh_keys(username=user.username)
            except UserNotFound:
                pass

        if not exclude_root:
            users.append(
                UserDataUser(
                    username="root",
                    user_type=UserDataUserOrigin.ROOT,
                    ssh_keys=get_ssh_keys(username=user.username),
                )
            )

    return users


def create_user(
    username: str,
    password: Optional[str] = None,
    directmemberof: Optional[list[str]] = None,
    displayname: Optional[str] = None,
) -> None:

    if is_username_forbidden(username):
        raise UsernameForbidden

    if not re.match(r"^[a-z_][a-z0-9_]+$", username):
        raise UsernameNotAlphanumeric

    if len(username) >= 32:
        raise UsernameTooLong

    if password:
        logger.error(PLEASE_UPDATE_APP_TEXT)

    if (
        displayname and len(displayname) >= 32
    ):  # we don't know the limitations of each service
        raise DisplaynameTooLong

    # need to maintain the logic of the old repository, since ssh management uses it.
    if not isinstance(ACTIVE_USERS_PROVIDER, JsonUserRepository):
        try:
            JsonUserRepository.create_user(
                username=username, password=str(uuid.uuid4())
            )  # random password for legacy
        except (UserAlreadyExists, InvalidConfiguration):
            pass

    ACTIVE_USERS_PROVIDER.create_user(
        username=username,
        directmemberof=directmemberof,
        displayname=displayname,
    )


def delete_user(username: str) -> None:
    if username == "root":
        raise UserIsProtected

    try:
        user = ACTIVE_USERS_PROVIDER.get_user_by_username(username=username)
    except UserNotFound:
        raise UserNotFound
    finally:
        # need to maintain the logic of the old repository, since ssh management uses it.
        if not isinstance(ACTIVE_USERS_PROVIDER, JsonUserRepository):
            try:
                JsonUserRepository.delete_user(username=username)
            except (UserNotFound, UserIsProtected):
                pass

    if user.user_type == UserDataUserOrigin.PRIMARY:
        raise UserIsProtected

    ACTIVE_USERS_PROVIDER.delete_user(username=username)


def update_user(
    username: str,
    password: Optional[str] = None,
    directmemberof: Optional[list[str]] = None,
    displayname: Optional[str] = None,
) -> None:

    if password:
        raise SelfPrivacyAppIsOutdate

    if username == "root":
        raise UserIsProtected

    if (
        displayname and len(displayname) >= 512
    ):  # we don't know the limitations of each service
        raise DisplaynameTooLong

    if directmemberof:
        user = ACTIVE_USERS_PROVIDER.get_user_by_username(username=username)

        groups_to_add = [item for item in directmemberof if item not in user.directmemberof]  # type: ignore
        groups_to_delete = [item for item in user.directmemberof if item not in directmemberof]  # type: ignore

        if groups_to_add:
            for group in groups_to_add:
                ACTIVE_USERS_PROVIDER.add_users_to_group(group_name=group, users=[username])

        if groups_to_delete:
            for group in groups_to_delete:
                ACTIVE_USERS_PROVIDER.remove_users_from_group(group_name=group, users=[username])

    ACTIVE_USERS_PROVIDER.update_user(
        username=username,
        displayname=displayname,
    )


def get_user_by_username(username: str) -> UserDataUser:
    if isinstance(ACTIVE_USERS_PROVIDER, JsonUserRepository):
        return ACTIVE_USERS_PROVIDER.get_user_by_username(username=username)

    if username == "root":
        return UserDataUser(
            username="root",
            user_type=UserDataUserOrigin.ROOT,
            ssh_keys=get_ssh_keys(username="root"),
        )

    user = ACTIVE_USERS_PROVIDER.get_user_by_username(username=username)

    try:
        user.ssh_keys = get_ssh_keys(username=user.username)
    except UserNotFound:
        pass

    return user


def generate_password_reset_link(username: str) -> str:
    if isinstance(ACTIVE_USERS_PROVIDER, JsonUserRepository):
        raise ApiUsingWrongUserRepository

    if username == "root":
        raise UserIsProtected

    return ACTIVE_USERS_PROVIDER.generate_password_reset_link(username=username)


def get_groups() -> list[Group]:
    if isinstance(ACTIVE_USERS_PROVIDER, JsonUserRepository):
        raise ApiUsingWrongUserRepository

    return ACTIVE_USERS_PROVIDER.get_groups()
