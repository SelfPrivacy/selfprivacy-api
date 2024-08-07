"""Users"""

# pylint: disable=too-few-public-methods
import typing
import strawberry

from selfprivacy_api.graphql.common_types.user import (
    User,
    get_user_by_username,
    get_users,
)
from selfprivacy_api.graphql import IsAuthenticated


@strawberry.type
class Users:
    @strawberry.field(permission_classes=[IsAuthenticated])
    def get_user(self, username: str) -> typing.Optional[User]:
        """Get users"""
        return get_user_by_username(username)

    all_users: typing.List[User] = strawberry.field(
        permission_classes=[IsAuthenticated], resolver=get_users
    )
