"""Actions to manage the users."""

import gettext
import logging
import re
import uuid
from typing import Optional

from selfprivacy_api.actions.email_passwords import (
    add_email_password,
    delete_all_email_passwords_hashes,
    update_legacy_email_password_hash,
)
from selfprivacy_api.actions.ssh import get_ssh_keys
from selfprivacy_api.models.group import Group, get_default_grops
from selfprivacy_api.models.user import UserDataUser, UserDataUserOrigin
from selfprivacy_api.repositories.users import ACTIVE_USERS_PROVIDER
from selfprivacy_api.repositories.users.exceptions import (
    DisplaynameTooLong,
    UserAlreadyExists,
    UserIsProtected,
    UsernameForbidden,
    UsernameNotAlphanumeric,
    UsernameTooLong,
    UserNotFound,
)
from selfprivacy_api.repositories.users.json_user_repository import JsonUserRepository
from selfprivacy_api.repositories.users.kanidm_user_repository import SP_DEFAULT_GROUPS
from selfprivacy_api.utils import (
    FORBIDDEN_PREFIXES,
    FORBIDDEN_USERNAMES,
    is_username_forbidden,
)
from selfprivacy_api.utils.localization import (
    DEFAULT_LOCALE,
    TranslateSystemMessage as t,
)
from selfprivacy_api.utils.strings import PLEASE_UPDATE_APP_TEXT

logger = logging.getLogger(__name__)

_ = gettext.gettext


class ApiUsingWrongUserRepository(Exception):
    """
    API is using a too old or unfinished user repository. Are you debugging?
    """

    def __init__(self):
        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_("API is using a too old or unfinished user repository"),
            locale=locale,
        )


async def get_users(
    exclude_primary: bool = False,
    exclude_root: bool = False,
) -> list[UserDataUser]:
    users = await ACTIVE_USERS_PROVIDER.get_users(
        exclude_primary=exclude_primary, exclude_root=exclude_root
    )

    if not ACTIVE_USERS_PROVIDER == JsonUserRepository:
        for user in users:
            try:
                user.ssh_keys = get_ssh_keys(username=user.username)
            except UserNotFound:
                pass

        if not exclude_root:
            root_user = UserDataUser(
                username="root",
                user_type=UserDataUserOrigin.ROOT,
                ssh_keys=get_ssh_keys(username="root"),
            )
            users.append(root_user)

    return users


async def create_user(
    username: str,
    password: Optional[str] = None,
    directmemberof: Optional[list[str]] = None,
    displayname: Optional[str] = None,
) -> None:

    if is_username_forbidden(username):
        raise UsernameForbidden(
            forbudden_usernames=FORBIDDEN_USERNAMES,
            forbudden_prefixes=FORBIDDEN_PREFIXES,
        )

    regex_pattern = r"^[a-z_][a-z0-9_]+$"
    if not re.match(regex_pattern, username):
        raise UsernameNotAlphanumeric(regex_pattern=regex_pattern)

    if len(username) >= 32:
        raise UsernameTooLong

    if password:
        logger.warning(PLEASE_UPDATE_APP_TEXT)

        add_email_password(
            username=username,
            password=password,
            with_created_at=True,
        )

    if displayname and len(displayname) >= 255:
        raise DisplaynameTooLong

    if not ACTIVE_USERS_PROVIDER == JsonUserRepository:
        try:
            await JsonUserRepository.create_user(
                username=username, password=str(uuid.uuid4())
            )  # random password for legacy repo
        except UserAlreadyExists:
            pass

    await ACTIVE_USERS_PROVIDER.create_user(
        username=username,
        directmemberof=directmemberof if directmemberof else SP_DEFAULT_GROUPS,
        displayname=displayname,
        password=password,
    )


async def delete_user(username: str) -> None:
    if username == "root":
        raise UserIsProtected(account_type="root")

    try:
        user = await ACTIVE_USERS_PROVIDER.get_user_by_username(username=username)
    except UserNotFound:
        raise UserNotFound
    finally:
        if not ACTIVE_USERS_PROVIDER == JsonUserRepository:
            try:
                await JsonUserRepository.delete_user(username=username)
            except (UserNotFound, UserIsProtected):
                pass

    if (
        user
        and ACTIVE_USERS_PROVIDER == JsonUserRepository
        and user.user_type == UserDataUserOrigin.PRIMARY
    ):
        raise UserIsProtected(account_type="primary")

    delete_all_email_passwords_hashes(username=username)

    await ACTIVE_USERS_PROVIDER.delete_user(username=username)


async def update_user(
    username: str,
    directmemberof: Optional[list[str]] = None,
    displayname: Optional[str] = None,
    password: Optional[str] = None,
) -> None:

    if password:
        logger.warning(PLEASE_UPDATE_APP_TEXT)

        update_legacy_email_password_hash(
            username=username,
            password=password,
            with_created_at=True,
        )

    if username == "root":
        raise UserIsProtected(account_type="root")

    if displayname:
        if ACTIVE_USERS_PROVIDER == JsonUserRepository:
            raise ApiUsingWrongUserRepository
        if len(displayname) >= 255:
            raise DisplaynameTooLong

        await ACTIVE_USERS_PROVIDER.update_user(
            username=username,
            displayname=displayname,
        )

    if directmemberof:
        if ACTIVE_USERS_PROVIDER == JsonUserRepository:
            raise ApiUsingWrongUserRepository

        user = await ACTIVE_USERS_PROVIDER.get_user_by_username(username=username)

        groups_to_add = [item for item in directmemberof if item not in user.directmemberof]  # type: ignore
        groups_to_delete = [item for item in user.directmemberof if item not in directmemberof]  # type: ignore

        if groups_to_add:
            for group in groups_to_add:

                if group in get_default_grops():
                    continue

                await ACTIVE_USERS_PROVIDER.add_users_to_group(
                    group_name=group, users=[username]
                )

        if groups_to_delete:
            for group in groups_to_delete:

                if group in get_default_grops():
                    continue

                await ACTIVE_USERS_PROVIDER.remove_users_from_group(
                    group_name=group, users=[username]
                )


async def get_user_by_username(username: str) -> Optional[UserDataUser]:
    if username == "root":
        return UserDataUser(
            username="root",
            user_type=UserDataUserOrigin.ROOT,
            ssh_keys=get_ssh_keys(username="root"),
        )

    user = await ACTIVE_USERS_PROVIDER.get_user_by_username(username=username)

    if user:
        try:
            user.ssh_keys = get_ssh_keys(username=user.username)
        except UserNotFound:
            pass

    return user


async def generate_password_reset_link(username: str) -> str:
    if ACTIVE_USERS_PROVIDER == JsonUserRepository:
        raise ApiUsingWrongUserRepository

    if username == "root":
        raise UserIsProtected(account_type="root")

    return await ACTIVE_USERS_PROVIDER.generate_password_reset_link(username=username)


async def get_groups() -> list[Group]:
    if ACTIVE_USERS_PROVIDER == JsonUserRepository:
        raise ApiUsingWrongUserRepository

    return await ACTIVE_USERS_PROVIDER.get_groups()
