import typing
from enum import Enum

import strawberry

from selfprivacy_api.actions.users import (
    get_user_by_username as actions_get_user_by_username,
)
from selfprivacy_api.actions.users import get_users as actions_get_users

from selfprivacy_api.graphql.mutations.mutation_interface import (
    MutationReturnInterface,
)


@strawberry.type
class UserRepositoryError(Exception):
    """Error occurred during repo query"""

    error: str


@strawberry.enum
class UserType(Enum):
    NORMAL = "NORMAL"
    PRIMARY = "PRIMARY"
    ROOT = "ROOT"


@strawberry.type
class User:
    user_type: UserType
    username: str
    # userHomeFolderspace: UserHomeFolderUsage
    ssh_keys: typing.List[str] = strawberry.field(default_factory=list)


@strawberry.type
class UserMutationReturn(MutationReturnInterface):
    """Return type for user mutation"""

    user: typing.Optional[User] = None


def get_user_by_username(username: str) -> typing.Optional[User]:
    user = actions_get_user_by_username(username=username)
    if user is None:
        return None

    return User(
        user_type=UserType(user.origin.value),
        username=user.username,
        ssh_keys=user.ssh_keys,
    )


def get_users() -> typing.List[User]:
    """Get users"""
    users = actions_get_users(exclude_root=True)
    return [
        User(
            user_type=UserType(user.origin.value),
            username=user.username,
            ssh_keys=user.ssh_keys,
        )
        for user in users
    ]
