"""Users"""
# pylint: disable=too-few-public-methods
import typing
import strawberry

from selfprivacy_api.graphql.common_types.user import (
    User,
    ensure_ssh_and_users_fields_exist,
    get_user_by_username,
)
from selfprivacy_api.utils import ReadUserData
from selfprivacy_api.graphql import IsAuthenticated


def get_users() -> typing.List[User]:
    """Get users"""
    user_list = []
    with ReadUserData() as data:
        ensure_ssh_and_users_fields_exist(data)

        for user in data["users"]:
            user_list.append(get_user_by_username(user["username"]))

        user_list.append(get_user_by_username(data["username"]))

        return user_list


@strawberry.type
class Users:
    @strawberry.field(permission_classes=[IsAuthenticated])
    def get_user(self, username: str) -> typing.Optional[User]:
        """Get users"""
        return get_user_by_username(username)

    all_users: typing.List[User] = strawberry.field(
        permission_classes=[IsAuthenticated], resolver=get_users
    )
