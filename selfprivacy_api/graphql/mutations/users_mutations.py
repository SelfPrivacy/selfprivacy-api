"""Users management module"""

# pylint: disable=too-few-public-methods
from typing import Optional
import gettext

import strawberry
from strawberry.types import Info

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
    ApiUsingWrongUserRepository,
    create_user as create_user_action,
    delete_user as delete_user_action,
    update_user as update_user_action,
    generate_password_reset_link as generate_password_reset_link_action,
)
from selfprivacy_api.repositories.users.exceptions import (
    DisplaynameTooLong,
    NoPasswordResetLinkFoundInResponse,
    PasswordIsEmpty,
    UserOrGroupNotFound,
    UsernameForbidden,
    InvalidConfiguration,
    UserAlreadyExists,
    UserIsProtected,
    UsernameNotAlphanumeric,
    UsernameTooLong,
    UserNotFound,
)
from selfprivacy_api.repositories.users.exceptions_kanidm import (
    FailedToGetValidKanidmToken,
    KanidmDidNotReturnAdminPassword,
    KanidmQueryError,
    KanidmReturnEmptyResponse,
    KanidmReturnUnknownResponseType,
    KanidmCliSubprocessError,
)
from selfprivacy_api.utils.localization import TranslateSystemMessage as t
from selfprivacy_api.utils.strings import PLEASE_UPDATE_APP_TEXT

_ = gettext.gettext

FAILED_TO_SETUP_SSO_PASSWORD_TEXT = _(
    "New password applied an an email password. To use Single Sign On, please update the SelfPrivacy app."
)


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
    password: Optional[str] = None
    display_name: Optional[str] = None


@strawberry.input
class SshMutationInput:
    """Input type for ssh mutation"""

    username: str
    ssh_key: str


@strawberry.type
class UsersMutations:
    """Mutations change user settings"""

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def create_user(self, user: UserMutationInput, info: Info) -> UserMutationReturn:
        locale = info.context["locale"]

        try:
            create_user_action(
                username=user.username,
                password=user.password,
                directmemberof=user.directmemberof,
                displayname=user.display_name,
            )
        except (
            PasswordIsEmpty,
            UsernameNotAlphanumeric,
            UsernameTooLong,
            InvalidConfiguration,
            KanidmDidNotReturnAdminPassword,
            KanidmQueryError,
            DisplaynameTooLong,
            KanidmCliSubprocessError,
            FailedToGetValidKanidmToken,
        ) as error:
            return return_failed_mutation_return(
                message=error.get_error_message(locale=locale),
            )
        except UsernameForbidden as error:
            return return_failed_mutation_return(
                message=error.get_error_message(locale=locale),
                code=409,
                username=user.username,
            )
        except UserAlreadyExists as error:
            return return_failed_mutation_return(
                message=error.get_error_message(locale=locale),
                code=409,
                username=user.username,
            )

        if user.password:
            return UserMutationReturn(
                success=True,
                message=f"{t.translate(text=FAILED_TO_SETUP_SSO_PASSWORD_TEXT, locale=locale)} {t.translate(text=PLEASE_UPDATE_APP_TEXT, locale=locale)}",
                code=201,
                user=get_user_by_username(user.username),
            )

        return UserMutationReturn(
            success=True,
            message=t.translate(text=_("User created"), locale=locale),
            code=201,
            user=get_user_by_username(user.username),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def delete_user(self, username: str, info: Info) -> GenericMutationReturn:
        locale = info.context["locale"]

        try:
            delete_user_action(username)
        except (UserNotFound, UserOrGroupNotFound) as error:
            return GenericMutationReturn(
                success=False,
                message=error.get_error_message(locale=locale),
                code=404,
            )
        except UserIsProtected as error:
            return GenericMutationReturn(
                success=False,
                code=400,
                message=error.get_error_message(locale=locale),
            )
        except (
            KanidmDidNotReturnAdminPassword,
            KanidmQueryError,
            KanidmCliSubprocessError,
            FailedToGetValidKanidmToken,
        ) as error:
            return GenericMutationReturn(
                success=False,
                code=500,
                message=error.get_error_message(locale=locale),
            )

        return GenericMutationReturn(
            success=True,
            message=t.translate(text=_("User deleted"), locale=locale),
            code=200,
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def update_user(self, user: UserMutationInput, info: Info) -> UserMutationReturn:
        """Update user mutation"""

        locale = info.context["locale"]
        try:
            update_user_action(
                username=user.username,
                password=user.password,
                directmemberof=user.directmemberof,
                displayname=user.display_name,
            )
        except (
            PasswordIsEmpty,
            KanidmDidNotReturnAdminPassword,
            KanidmQueryError,
            DisplaynameTooLong,
            KanidmCliSubprocessError,
            FailedToGetValidKanidmToken,
            ApiUsingWrongUserRepository,
        ) as error:
            return return_failed_mutation_return(
                message=error.get_error_message(locale=locale),
                username=user.username,
            )
        except (UserNotFound, UserOrGroupNotFound) as error:
            return return_failed_mutation_return(
                message=error.get_error_message(locale=locale),
                code=404,
                username=user.username,
            )

        if user.password:
            return UserMutationReturn(
                success=True,
                message=f"{t.translate(text=_(FAILED_TO_SETUP_SSO_PASSWORD_TEXT), locale=locale)} {t.translate(text=_(PLEASE_UPDATE_APP_TEXT), locale=locale)}",
                code=200,
                user=get_user_by_username(user.username),
            )

        return UserMutationReturn(
            success=True,
            message=t.translate(text=_("User updated"), locale=locale),
            code=200,
            user=get_user_by_username(user.username),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def add_ssh_key(
        self, ssh_input: SshMutationInput, info: Info
    ) -> UserMutationReturn:
        """Add a new ssh key"""

        locale = info.context["locale"]
        try:
            create_ssh_key_action(ssh_input.username, ssh_input.ssh_key)
        except KeyAlreadyExists as error:
            return return_failed_mutation_return(
                message=error.get_error_message(locale=locale),
                code=409,
            )
        except InvalidPublicKey as error:
            return return_failed_mutation_return(
                message=error.get_error_message(locale=locale),
            )
        except UserNotFound as error:
            return return_failed_mutation_return(
                message=error.get_error_message(locale=locale),
                code=404,
            )
        except Exception as error:  # TODO why?
            return return_failed_mutation_return(
                message=str(error),
                code=500,
            )

        return UserMutationReturn(
            success=True,
            message=t.translate(
                text=_("New SSH key successfully written"), locale=locale
            ),
            code=201,
            user=get_user_by_username(ssh_input.username),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def remove_ssh_key(
        self, ssh_input: SshMutationInput, info: Info
    ) -> UserMutationReturn:
        """Remove ssh key from user"""

        locale = info.context["locale"]
        try:
            remove_ssh_key_action(ssh_input.username, ssh_input.ssh_key)
        except (KeyNotFound, UserNotFound) as error:
            return return_failed_mutation_return(
                message=error.get_error_message(locale=locale),
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
            message=t.translate(text=_("SSH key successfully removed"), locale=locale),
            code=200,
            user=get_user_by_username(ssh_input.username),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def generate_password_reset_link(
        self, username: str, info: Info
    ) -> PasswordResetLinkReturn:

        locale = info.context["locale"]
        try:
            password_reset_link = generate_password_reset_link_action(username=username)
        except (UserNotFound, UserOrGroupNotFound) as error:
            return PasswordResetLinkReturn(
                success=False,
                message=error.get_error_message(locale=locale),
                code=404,
            )
        except UserIsProtected as error:
            return PasswordResetLinkReturn(
                success=False,
                message=error.get_error_message(locale=locale),
                code=400,
            )
        except (
            NoPasswordResetLinkFoundInResponse,
            KanidmDidNotReturnAdminPassword,
            KanidmReturnUnknownResponseType,
            KanidmReturnEmptyResponse,
            KanidmQueryError,
            KanidmCliSubprocessError,
            FailedToGetValidKanidmToken,
            ApiUsingWrongUserRepository,
        ) as error:
            return PasswordResetLinkReturn(
                success=False,
                code=500,
                message=error.get_error_message(locale=locale),
            )

        return PasswordResetLinkReturn(
            success=True,
            message=t.translate(text=_("Link successfully created"), locale=locale),
            code=200,
            password_reset_link=password_reset_link,
        )
