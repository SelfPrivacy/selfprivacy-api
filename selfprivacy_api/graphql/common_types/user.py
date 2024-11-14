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


@strawberry.enum
class UserType(Enum):
    NORMAL = "NORMAL"
    PRIMARY = "PRIMARY"
    ROOT = "ROOT"


@strawberry.type
class User:
    displayname: str
    username: str
    user_type: UserType
    ssh_keys: typing.List[str] = strawberry.field(default_factory=list)
    uuid: typing.Optional[str] = None
    email: typing.Optional[str] = None
    directmemberof: typing.Optional[typing.List[str]] = strawberry.field(
        default_factory=list
    )
    memberof: typing.Optional[typing.List[str]] = strawberry.field(default_factory=list)
    # userHomeFolderspace: UserHomeFolderUsage


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
        uuid=user.uuid,
        displayname=(user.displayname if user.displayname else user.username),
        email=user.email,
        directmemberof=user.directmemberof,
        memberof=user.memberof,
    )


def get_users() -> typing.List[User]:
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
