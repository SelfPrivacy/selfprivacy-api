import typing
from enum import Enum
import strawberry

from selfprivacy_api.utils import ReadUserData
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

    user: typing.Optional[User]


def ensure_ssh_and_users_fields_exist(data):
    if "ssh" not in data:
        data["ssh"] = []
        data["ssh"]["rootKeys"] = []

    elif data["ssh"].get("rootKeys") is None:
        data["ssh"]["rootKeys"] = []

    if "sshKeys" not in data:
        data["sshKeys"] = []

    if "users" not in data:
        data["users"] = []


def get_user_by_username(username: str) -> typing.Optional[User]:
    with ReadUserData() as data:
        ensure_ssh_and_users_fields_exist(data)

        if username == "root":
            return User(
                user_type=UserType.ROOT,
                username="root",
                ssh_keys=data["ssh"]["rootKeys"],
            )

        if username == data["username"]:
            return User(
                user_type=UserType.PRIMARY,
                username=username,
                ssh_keys=data["sshKeys"],
            )

        for user in data["users"]:
            if user["username"] == username:
                if "sshKeys" not in user:
                    user["sshKeys"] = []

                return User(
                    user_type=UserType.NORMAL,
                    username=username,
                    ssh_keys=user["sshKeys"],
                )

        return None
