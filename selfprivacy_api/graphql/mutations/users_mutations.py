#!/usr/bin/env python3
"""Users management module"""
# pylint: disable=too-few-public-methods
from typing import Optional
import strawberry

from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.graphql.common_types.user import (
    UserMutationReturn,
    get_user_by_username,
)
from selfprivacy_api.actions.ssh import (
    InvalidPublicKey,
    KeyAlreadyExists,
    KeyNotFound,
    create_ssh_key as create_ssh_key_action,
    remove_ssh_key as remove_ssh_key_action,
)
from selfprivacy_api.graphql.mutations.mutation_interface import (
    GenericMutationReturn,
)
from selfprivacy_api.actions.users import (
    create_user as create_user_action,
    delete_user as delete_user_action,
    update_user as update_user_action,
    generate_password_reset_link as generate_password_reset_link_action,
)
from selfprivacy_api.repositories.users.exceptions import (
    PasswordIsEmpty,
    UsernameForbidden,
    InvalidConfiguration,
    UserAlreadyExists,
    UserIsProtected,
    UsernameNotAlphanumeric,
    UsernameTooLong,
    UserNotFound,
    SelfPrivacyAppIsOutdate,
)
from selfprivacy_api import PLEASE_UPDATE_APP_TEXT


@strawberry.input
class UserMutationInput:
    """Input type for user mutation"""

    username: str
    password: Optional[str] = None
    displayname: Optional[str] = None
    email: Optional[str] = None
    directmemberof: Optional[list[str]] = None
    memberof: Optional[list[str]] = None


@strawberry.input
class SshMutationInput:
    """Input type for ssh mutation"""

    username: str
    ssh_key: str


@strawberry.type
class UsersMutations:
    """Mutations change user settings"""

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def create_user(self, user: UserMutationInput) -> UserMutationReturn:
        try:
            create_user_action(
                username=user.username,
                password=user.password,
                displayname=user.displayname,
                email=user.email,
                directmemberof=user.directmemberof,
                memberof=user.memberof,
            )
        except PasswordIsEmpty as e:
            return UserMutationReturn(
                success=False,
                message=str(e),
                code=400,
            )
        except UsernameForbidden as e:
            return UserMutationReturn(
                success=False,
                message=str(e),
                code=409,
            )
        except UsernameNotAlphanumeric as e:
            return UserMutationReturn(
                success=False,
                message=str(e),
                code=400,
            )
        except UsernameTooLong as e:
            return UserMutationReturn(
                success=False,
                message=str(e),
                code=400,
            )
        except InvalidConfiguration as e:
            return UserMutationReturn(
                success=False,
                message=str(e),
                code=400,
            )
        except UserAlreadyExists as e:
            return UserMutationReturn(
                success=False,
                message=str(e),
                code=409,
                user=get_user_by_username(user.username),
            )

        return UserMutationReturn(
            success=True,
            message=PLEASE_UPDATE_APP_TEXT if user.password else "User created",
            code=201,
            user=get_user_by_username(user.username),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def delete_user(self, username: str) -> GenericMutationReturn:
        try:
            delete_user_action(username)
        except UserNotFound as e:
            return GenericMutationReturn(
                success=False,
                message=str(e),
                code=404,
            )
        except UserIsProtected as e:
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
            update_user_action(
                username=user.username,
                password=user.password,
                displayname=user.displayname,
                email=user.email,
                directmemberof=user.directmemberof,
                memberof=user.memberof,
            )
        except PasswordIsEmpty as e:
            return UserMutationReturn(
                success=False,
                message=str(e),
                code=400,
            )
        except UserNotFound as e:
            return UserMutationReturn(
                success=False,
                message=str(e),
                code=404,
            )
        except SelfPrivacyAppIsOutdate:
            return UserMutationReturn(
                success=False,
                message=f"Error: Failed to change password. {PLEASE_UPDATE_APP_TEXT}",
                code=400,
            )

        return UserMutationReturn(
            success=True,
            message="User updated",
            code=200,
            user=get_user_by_username(user.username),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def add_ssh_key(self, ssh_input: SshMutationInput) -> UserMutationReturn:
        """Add a new ssh key"""

        try:
            create_ssh_key_action(ssh_input.username, ssh_input.ssh_key)
        except KeyAlreadyExists:
            return UserMutationReturn(
                success=False,
                message="Key already exists",
                code=409,
            )
        except InvalidPublicKey:
            return UserMutationReturn(
                success=False,
                message="Invalid key type. Only ssh-ed25519, ssh-rsa and ecdsa are supported",
                code=400,
            )
        except UserNotFound:
            return UserMutationReturn(
                success=False,
                message="User not found",
                code=404,
            )
        except Exception as e:  # TODO why?
            return UserMutationReturn(
                success=False,
                message=str(e),
                code=500,
            )

        return UserMutationReturn(
            success=True,
            message="New SSH key successfully written",
            code=201,
            user=get_user_by_username(ssh_input.username),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def remove_ssh_key(self, ssh_input: SshMutationInput) -> UserMutationReturn:
        """Remove ssh key from user"""

        try:
            remove_ssh_key_action(ssh_input.username, ssh_input.ssh_key)
        except KeyNotFound:
            return UserMutationReturn(
                success=False,
                message="Key not found",
                code=404,
            )
        except UserNotFound:
            return UserMutationReturn(
                success=False,
                message="User not found",
                code=404,
            )
        except Exception as e:  # TODO why?
            return UserMutationReturn(
                success=False,
                message=str(e),
                code=500,
            )

        return UserMutationReturn(
            success=True,
            message="SSH key successfully removed",
            code=200,
            user=get_user_by_username(ssh_input.username),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def generate_password_reset_link(username: str) -> UserMutationReturn:
        try:
            password_reset_link = generate_password_reset_link_action(username=username)
        except UserNotFound:
            return UserMutationReturn(
                success=False,
                message="User not found",
                code=404,
            )

        return UserMutationReturn(
            success=True,
            message="Link successfully created",
            code=200,
            password_reset_link=password_reset_link,
        )
