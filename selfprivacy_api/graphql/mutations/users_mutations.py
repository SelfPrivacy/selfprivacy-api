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
import selfprivacy_api.actions.users as users_actions


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
        try:
            users_actions.create_user(user.username, user.password)
        except users_actions.PasswordIsEmpty as e:
            return UserMutationReturn(
                success=False,
                message=str(e),
                code=400,
            )
        except users_actions.UsernameForbidden as e:
            return UserMutationReturn(
                success=False,
                message=str(e),
                code=409,
            )
        except users_actions.UsernameNotAlphanumeric as e:
            return UserMutationReturn(
                success=False,
                message=str(e),
                code=400,
            )
        except users_actions.UsernameTooLong as e:
            return UserMutationReturn(
                success=False,
                message=str(e),
                code=400,
            )
        except users_actions.UserAlreadyExists as e:
            return UserMutationReturn(
                success=False,
                message=str(e),
                code=409,
                user=get_user_by_username(user.username),
            )

        return UserMutationReturn(
            success=True,
            message="User created",
            code=201,
            user=get_user_by_username(user.username),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def delete_user(self, username: str) -> GenericMutationReturn:
        try:
            users_actions.delete_user(username)
        except users_actions.UserNotFound as e:
            return GenericMutationReturn(
                success=False,
                message=str(e),
                code=404,
            )
        except users_actions.UserIsProtected as e:
            return GenericMutationReturn(
                success=False,
                message=str(e),
                code=400,
            )

        return GenericMutationReturn(
            success=True,
            message="User deleted",
            code=200,
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def update_user(self, user: UserMutationInput) -> UserMutationReturn:
        """Update user mutation"""
        try:
            users_actions.update_user(user.username, user.password)
        except users_actions.PasswordIsEmpty as e:
            return UserMutationReturn(
                success=False,
                message=str(e),
                code=400,
            )
        except users_actions.UserNotFound as e:
            return UserMutationReturn(
                success=False,
                message=str(e),
                code=404,
            )

        return UserMutationReturn(
            success=True,
            message="User updated",
            code=200,
            user=get_user_by_username(user.username),
        )
