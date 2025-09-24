"""Users"""

# pylint: disable=too-few-public-methods
from typing import Optional, List
from opentelemetry import trace

import strawberry

from selfprivacy_api.graphql.common_types.user import (
    User,
    get_user_by_username,
    get_users,
)
from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.repositories.users.exceptions import UserNotFound

tracer = trace.get_tracer(__name__)


@strawberry.type
class Users:
    @strawberry.field(permission_classes=[IsAuthenticated])
    async def get_user(self, username: str) -> Optional[User]:
        """Get users"""
        with tracer.start_as_current_span(
            "Users.get_user", attributes={"username": username}
        ):
            try:
                return await get_user_by_username(username)
            except UserNotFound:
                return None

    all_users: List[User] = strawberry.field(
        permission_classes=[IsAuthenticated], resolver=get_users
    )
