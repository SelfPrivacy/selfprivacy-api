#!/usr/bin/env python3
"""Users management module"""
# pylint: disable=too-few-public-methods
from typing import Optional
import strawberry

from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.graphql.common_types.user import (
    PasswordResetLinkReturn,
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
    NoPasswordResetLinkFoundInResponse,
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
from selfprivacy_api.repositories.users.kanidm_user_repository import KanidmDidNotReturnAdminPassword


FAILED_TO_SETUP_PASSWORD_TEXT = "Failed to set a password for a user. The problem occurred due to an old version of the SelfPrivacy app."


def return_failed_mutation_return(
    message: str,
    code: int = 400,
    username: Optional[str] = None,
) -> UserMutationReturn:
    return UserMutationReturn(
        success=False,
        message=str(message),
        code=code,
        user=get_user_by_username(username) if username else None,
    )


@strawberry.input
class UserMutationInput:
    """Input type for user mutation"""

    username: str
    directmemberof: Optional[list[str]] = strawberry.field(default_factory=list)
    memberof: Optional[list[str]] = strawberry.field(default_factory=list)
    password: Optional[str] = None
    displayname: Optional[str] = None
    email: Optional[str] = None


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
        except (
            PasswordIsEmpty,
            UsernameNotAlphanumeric,
            UsernameTooLong,
            InvalidConfiguration,
            KanidmDidNotReturnAdminPassword,
        ) as error:
            return return_failed_mutation_return(
                message=error.get_error_message(),
            )
        except UsernameForbidden as error:
            return return_failed_mutation_return(
                message=error.get_error_message(),
                code=409,
                username=user.username,
            )
        except UserAlreadyExists as error:
            return return_failed_mutation_return(
                message=error.get_error_message(),
                code=409,
            )

        if user.password:
            return return_failed_mutation_return(
                message=f"{FAILED_TO_SETUP_PASSWORD_TEXT} {PLEASE_UPDATE_APP_TEXT}",
                code=201,
                username=user.username,
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
            delete_user_action(username)
        except UserNotFound as error:
            return GenericMutationReturn(
                success=False,
                message=error.get_error_message(),
                code=404,
            )
        except UserIsProtected as error:
            return GenericMutationReturn(
                success=False,
                code=400,
                message=error.get_error_message(),
            )
        except KanidmDidNotReturnAdminPassword as error:
            return GenericMutationReturn(
                success=False,
                code=500,
                message=error.get_error_message(),
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
        except (PasswordIsEmpty, SelfPrivacyAppIsOutdate, KanidmDidNotReturnAdminPassword) as error:
            return return_failed_mutation_return(
                message=error.get_error_message(),
            )
        except UserNotFound as error:
            return return_failed_mutation_return(
                message=error.get_error_message(),
                code=404,
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
        except KeyAlreadyExists as error:
            return return_failed_mutation_return(
                message=error.get_error_message(),
                code=409,
            )
        except InvalidPublicKey as error:
            return return_failed_mutation_return(
                message=error.get_error_message(),
            )
        except UserNotFound as error:
            return return_failed_mutation_return(
                message=error.get_error_message(),
                code=404,
            )
        except Exception as error:  # TODO why?
            return return_failed_mutation_return(
                message=str(error),
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
        except (KeyNotFound, UserNotFound) as error:
            return return_failed_mutation_return(
                message=error.get_error_message(),
                code=404,
            )
        except Exception as error:  # TODO why?
            return UserMutationReturn(
                success=False,
                message=str(error),
                code=500,
            )

        return UserMutationReturn(
            success=True,
            message="SSH key successfully removed",
            code=200,
            user=get_user_by_username(ssh_input.username),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def generate_password_reset_link(
        self, user: UserMutationInput
    ) -> PasswordResetLinkReturn:
        try:
            password_reset_link = generate_password_reset_link_action(
                username=user.username
            )
        except UserNotFound as error:
            return PasswordResetLinkReturn(
                success=False,
                message=error.get_error_message(),
                code=404,
            )
        except (NoPasswordResetLinkFoundInResponse, KanidmDidNotReturnAdminPassword) as error:
            return PasswordResetLinkReturn(
                success=False,
                code=500,
                message=error.get_error_message(),
            )

        return PasswordResetLinkReturn(
            success=True,
            message="Link successfully created",
            code=200,
            password_reset_link=password_reset_link,
        )
