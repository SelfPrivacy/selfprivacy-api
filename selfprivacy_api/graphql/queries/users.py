# pylint: disable=too-few-public-methods

from typing import List, Optional

import strawberry
from opentelemetry import trace

from selfprivacy_api.exceptions.users import UserNotFound
from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.graphql.common_types.kanidm_credential_type import (
    get_minimum_kanidm_credential_type,
)
from selfprivacy_api.graphql.common_types.user import (
    User,
    get_user_by_username,
    get_users,
)
from selfprivacy_api.models.kanidm_credential_type import KanidmCredentialType

tracer = trace.get_tracer(__name__)


@strawberry.type
class Users:
    @strawberry.field(permission_classes=[IsAuthenticated])
    async def minimum_credential_type(self) -> KanidmCredentialType:
        """Get the minimum Kanidm credential type."""
        return await get_minimum_kanidm_credential_type()

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
