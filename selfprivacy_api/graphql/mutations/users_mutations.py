#!/usr/bin/env python3
"""Users management module"""
# pylint: disable=too-few-public-methods
import strawberry
from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.graphql.common_types.user import (
    UserMutationReturn,
    get_user_by_username,
)
from selfprivacy_api.graphql.mutations.mutation_interface import (
    GenericMutationReturn,
)
from selfprivacy_api.graphql.mutations.users_utils import (
    create_user,
    delete_user,
    update_user,
)


@strawberry.input
class UserMutationInput:
    """Input type for user mutation"""

    username: str
    password: str


@strawberry.type
class UserMutations:
    """Mutations change user settings"""

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def create_user(self, user: UserMutationInput) -> UserMutationReturn:

        success, message, code = create_user(user.username, user.password)

        return UserMutationReturn(
            success=success,
            message=message,
            code=code,
            user=get_user_by_username(user.username),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def delete_user(self, username: str) -> GenericMutationReturn:
        success, message, code = delete_user(username)

        return GenericMutationReturn(
            success=success,
            message=message,
            code=code,
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def update_user(self, user: UserMutationInput) -> UserMutationReturn:
        """Update user mutation"""

        success, message, code = update_user(user.username, user.password)

        return UserMutationReturn(
            success=success,
            message=message,
            code=code,
            user=get_user_by_username(user.username),
        )
