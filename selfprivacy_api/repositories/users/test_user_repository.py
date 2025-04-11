import logging
import uuid
from typing import Optional

from selfprivacy_api.repositories.users.exceptions import (
    NoPasswordResetLinkFoundInResponse,
    UserAlreadyExists,
    UserNotFound,
    UserOrGroupNotFound,
)
from selfprivacy_api.repositories.users.abstract_user_repository import (
    AbstractUserRepository,
)
from selfprivacy_api.models.user import UserDataUser, UserDataUserOrigin
from selfprivacy_api.models.group import Group, get_default_groops
from selfprivacy_api.utils import get_domain

logger = logging.getLogger(__name__)

SP_ADMIN_GROUPS = ["sp.admins"]
SP_DEFAULT_GROUPS = ["sp.full_users"]


class TestUserRepository(AbstractUserRepository):
    _USERS_DB: dict[str, UserDataUser] = {}
    _GROUPS_DB: dict[str, Group] = {}

    @staticmethod
    def _remove_default_groups(groups: list[str]) -> list[str]:
        return [group for group in groups if group not in get_default_groops()]

    @staticmethod
    def _check_user_origin_by_memberof(memberof: list[str]) -> UserDataUserOrigin:
        if all(admin_group in memberof for admin_group in SP_ADMIN_GROUPS):
            return UserDataUserOrigin.PRIMARY
        return UserDataUserOrigin.NORMAL

    @staticmethod
    def _sync_group_membership(
        username: str, directmemberof: Optional[list[str]] = None
    ) -> None:
        for group in TestUserRepository._GROUPS_DB.values():
            if group.member and username in group.member:
                group.member.remove(username)

        if directmemberof:
            for group_name in directmemberof:
                if group_name not in TestUserRepository._GROUPS_DB:
                    TestUserRepository._GROUPS_DB[group_name] = Group(
                        name=group_name, member=[username]
                    )
                else:
                    group = TestUserRepository._GROUPS_DB[group_name]
                    if not group.member:
                        group.member = []
                    if username not in group.member:
                        group.member.append(username)

    @staticmethod
    def create_user(
        username: str,
        directmemberof: Optional[list[str]] = None,
        displayname: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        if username in TestUserRepository._USERS_DB:
            raise UserAlreadyExists

        directmemberof = directmemberof or []
        total_memberof = list(set(directmemberof + SP_DEFAULT_GROUPS))
        user_type = TestUserRepository._check_user_origin_by_memberof(total_memberof)

        new_user = UserDataUser(
            username=username,
            user_type=user_type,
            ssh_keys=[],
            directmemberof=directmemberof,
            memberof=total_memberof,
            displayname=displayname if displayname else username,
            email=f"{username}@{get_domain()}",
        )

        TestUserRepository._USERS_DB[username] = new_user
        TestUserRepository._sync_group_membership(username, directmemberof)

    @staticmethod
    def get_users(
        exclude_primary: bool = False,
        exclude_root: bool = False,
    ) -> list[UserDataUser]:
        all_users = []
        for user in TestUserRepository._USERS_DB.values():
            if exclude_primary and user.user_type == UserDataUserOrigin.PRIMARY:
                continue
            if exclude_root and user.username == "root":
                continue
            all_users.append(user)
        return all_users

    @staticmethod
    def delete_user(username: str) -> None:
        if username not in TestUserRepository._USERS_DB:
            raise UserNotFound

        del TestUserRepository._USERS_DB[username]

        for group in TestUserRepository._GROUPS_DB.values():
            if group.member and username in group.member:
                group.member.remove(username)

    @staticmethod
    def update_user(
        username: str,
        displayname: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        if username not in TestUserRepository._USERS_DB:
            raise UserNotFound

        user = TestUserRepository._USERS_DB[username]
        if displayname:
            user.displayname = displayname

        TestUserRepository._USERS_DB[username] = user

    @staticmethod
    def get_user_by_username(username: str) -> UserDataUser:
        if username not in TestUserRepository._USERS_DB:
            raise UserNotFound
        return TestUserRepository._USERS_DB[username]

    @staticmethod
    def generate_password_reset_link(username: str) -> str:
        if username not in TestUserRepository._USERS_DB:
            raise UserNotFound

        random_token = str(uuid.uuid4())
        if not random_token:
            raise NoPasswordResetLinkFoundInResponse

        return f"https://auth.{get_domain()}/ui/reset?token={random_token}"

    @staticmethod
    def get_groups() -> list[Group]:
        return list(TestUserRepository._GROUPS_DB.values())

    @staticmethod
    def add_users_to_group(users: list[str], group_name: str) -> None:
        if group_name not in TestUserRepository._GROUPS_DB:
            TestUserRepository._GROUPS_DB[group_name] = Group(
                name=group_name, member=[]
            )

        group = TestUserRepository._GROUPS_DB[group_name]
        if group.member is None:
            group.member = []

        for username in users:
            if username not in TestUserRepository._USERS_DB:
                raise UserOrGroupNotFound
            if username not in group.member:
                group.member.append(username)

            user = TestUserRepository._USERS_DB[username]
            if user.directmemberof is None:
                user.directmemberof = []
            if group_name not in user.directmemberof:
                user.directmemberof.append(group_name)

            total_memberof = list(set(user.directmemberof + SP_DEFAULT_GROUPS))
            user.memberof = total_memberof
            user.user_type = TestUserRepository._check_user_origin_by_memberof(
                user.memberof
            )
            TestUserRepository._USERS_DB[username] = user

        TestUserRepository._GROUPS_DB[group_name] = group

    @staticmethod
    def remove_users_from_group(users: list[str], group_name: str) -> None:
        if group_name not in TestUserRepository._GROUPS_DB:
            raise UserOrGroupNotFound

        group = TestUserRepository._GROUPS_DB[group_name]
        if group.member is None:
            group.member = []

        for username in users:
            if username not in TestUserRepository._USERS_DB:
                raise UserOrGroupNotFound
            if username in group.member:
                group.member.remove(username)

            user = TestUserRepository._USERS_DB[username]
            if user.directmemberof and group_name in user.directmemberof:
                user.directmemberof.remove(group_name)

            total_memberof = list(
                set((user.directmemberof or []) + SP_DEFAULT_GROUPS)
            )
            user.memberof = total_memberof
            user.user_type = TestUserRepository._check_user_origin_by_memberof(
                user.memberof
            )
            TestUserRepository._USERS_DB[username] = user

        TestUserRepository._GROUPS_DB[group_name] = group
