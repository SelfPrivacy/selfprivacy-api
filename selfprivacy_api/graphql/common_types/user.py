from typing import Optional
from enum import Enum

import strawberry

from selfprivacy_api.actions.users import (
    get_user_by_username as actions_get_user_by_username,
)
from selfprivacy_api.actions.users import get_users as actions_get_users

from selfprivacy_api.graphql.mutations.mutation_interface import (
    MutationReturnInterface,
)


@strawberry.enum
class UserType(Enum):
    NORMAL = "NORMAL"
    PRIMARY = "PRIMARY"
    ROOT = "ROOT"


@strawberry.type
class User:
    username: str

    ssh_keys: Optional[list[str]] = strawberry.field(default_factory=list)
    user_type: Optional[UserType] = None
    displayname: Optional[str] = None
    email: Optional[str] = None
    directmemberof: Optional[list[str]] = None
    memberof: Optional[list[str]] = None
    # userHomeFolderspace: UserHomeFolderUsage


@strawberry.type
class UserMutationReturn(MutationReturnInterface):
    """Return type for user mutation"""

    user: Optional[User] = None
    password_reset_link: Optional[str] = None


def get_user_by_username(username: str) -> Optional[User]:
    user = actions_get_user_by_username(username=username)
    if user is None:
        return None

    return User(
        username=user.username,
        ssh_keys=user.ssh_keys or [],
        user_type=user.user_type or None,
        displayname=user.displayname or None,
        email=user.email or None,
        directmemberof=user.directmemberof or None,
        memberof=user.memberof or None,
    )


def get_users() -> list[User]:
    """Get users"""
    users = actions_get_users(exclude_root=True)
    return [
        User(
            username=user.username,
            ssh_keys=user.ssh_keys or [],
            user_type=user.user_type or None,
            displayname=user.displayname or None,
            email=user.email or None,
            directmemberof=user.directmemberof or None,
            memberof=user.memberof or None,
        )
        for user in users
    ]
