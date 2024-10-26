import typing
from enum import Enum
import strawberry
from selfprivacy_api.repositories.users import ACTIVE_USERS_PROVIDER as users_actions

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
    user_type: UserType
    username: str
    # userHomeFolderspace: UserHomeFolderUsage
    ssh_keys: typing.List[str] = strawberry.field(default_factory=list)


@strawberry.type
class UserMutationReturn(MutationReturnInterface):
    """Return type for user mutation"""

    user: typing.Optional[User] = None


def get_user_by_username(username: str) -> typing.Optional[User]:
    user = users_actions.get_user_by_username(username=username)
    if user is None:
        return None

    return User(
        user_type=UserType(user.origin.value),
        username=user.username,
        ssh_keys=user.ssh_keys,
    )


def get_users() -> typing.List[User]:
    """Get users"""
    users = users_actions.get_users(exclude_root=True)
    return [
        User(
            user_type=UserType(user.origin.value),
            username=user.username,
            ssh_keys=user.ssh_keys,
        )
        for user in users
    ]
