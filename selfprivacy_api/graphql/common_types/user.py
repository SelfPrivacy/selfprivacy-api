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
    user_type: UserType

    ssh_keys: Optional[list[str]] = strawberry.field(default_factory=list)
    directmemberof: Optional[list[str]] = strawberry.field(default_factory=list)
    memberof: Optional[list[str]] = strawberry.field(default_factory=list)
    displayname: Optional[str] = None
    email: Optional[str] = None


@strawberry.type
class UserMutationReturn(MutationReturnInterface):
    """Return type for user mutation"""

    user: Optional[User] = None


@strawberry.type
class PasswordResetLinkReturn(MutationReturnInterface):
    """Return password reset link"""

    password_reset_link: Optional[str] = None


def get_user_by_username(username: str) -> Optional[User]:
    user = actions_get_user_by_username(username=username)
    if user is None:
        return None

    return User(
        username=user.username,
        user_type=UserType(user.user_type.value),
        ssh_keys=getattr(user, "ssh_keys", []),
        directmemberof=getattr(user, "directmemberof", []),
        memberof=getattr(user, "memberof", []),
        displayname=getattr(user, "displayname", None),
        email=getattr(user, "email", None),
    )


def get_users() -> list[User]:
    """Get users"""
    users = actions_get_users(exclude_root=True)
    return [
        User(
            username=user.username,
            user_type=UserType(user.user_type.value),
            ssh_keys=getattr(user, "ssh_keys", []),
            directmemberof=getattr(user, "directmemberof", []),
            memberof=getattr(user, "memberof", []),
            displayname=getattr(user, "displayname", None),
            email=getattr(user, "email", None),
        )
        for user in users
    ]
