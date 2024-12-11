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
from selfprivacy_api.repositories.users.exceptions_kanidm import (
    KanidmReturnUnknownResponseType,
    KanidmReturnEmptyResponse,
)


@strawberry.type
class Users:
    @strawberry.field(permission_classes=[IsAuthenticated])
    def get_user(self, username: str) -> typing.Optional[User]:
        """Get users"""
        try:
            return get_user_by_username(username)
        except (KanidmReturnUnknownResponseType, KanidmReturnEmptyResponse):
            pass  # TODO what todo ??

    all_users: typing.List[User] = strawberry.field(
        permission_classes=[IsAuthenticated], resolver=get_users
    )
