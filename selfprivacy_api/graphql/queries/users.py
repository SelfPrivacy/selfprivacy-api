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
from selfprivacy_api.repositories.users.exceptions import UserNotFound
from selfprivacy_api.actions.users import groups_list as action_groups_list


@strawberry.type
class Users:
    @strawberry.field(permission_classes=[IsAuthenticated])
    def get_user(self, username: str) -> typing.Optional[User]:
        """Get users"""

        try:
            return get_user_by_username(username)
        except UserNotFound:
            return None

    all_users: typing.List[User] = strawberry.field(
        permission_classes=[IsAuthenticated], resolver=get_users
    )

    @strawberry.field(permission_classes=[IsAuthenticated])
    def groups_list() -> list:
        return action_groups_list()
