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
    displayname: Optional[str] = None
    ssh_keys: list[str] = strawberry.field(default_factory=list)
    uuid: Optional[str] = None
    email: Optional[str] = None
    directmemberof: Optional[list[str]] = strawberry.field(default_factory=list)
    memberof: Optional[list[str]] = strawberry.field(default_factory=list)
    # userHomeFolderspace: UserHomeFolderUsage


@strawberry.type
class UserMutationReturn(MutationReturnInterface):
    """Return type for user mutation"""

    user: Optional[User] = None


def get_user_by_username(username: str) -> Optional[User]:
    user = actions_get_user_by_username(username=username)
    if user is None:
        return None

    return User(
        user_type=UserType(user.origin.value),
        username=user.username,
        ssh_keys=user.ssh_keys,
        uuid=user.uuid,
        displayname=(user.displayname if user.displayname else user.username),
        email=user.email,
        directmemberof=user.directmemberof,
        memberof=user.memberof,
    )


def get_users() -> list[User]:
    """Get users"""
    users = actions_get_users(exclude_root=True)
    return [
        User(
            user_type=UserType(user.origin.value),
            username=user.username,
            ssh_keys=user.ssh_keys,
            uuid=user.uuid,
            displayname=(user.displayname if user.displayname else user.username),
            email=user.email,
            directmemberof=user.directmemberof,
            memberof=user.memberof,
        )
        for user in users
    ]
