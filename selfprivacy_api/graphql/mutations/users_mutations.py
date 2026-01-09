"""Users management module"""

# pylint: disable=too-few-public-methods

import gettext
from typing import Optional

import strawberry
from opentelemetry import trace
from strawberry.types import Info

from selfprivacy_api.actions.ssh import (
    create_ssh_key as create_ssh_key_action,
    remove_ssh_key as remove_ssh_key_action,
)
from selfprivacy_api.actions.users import (
    create_user as create_user_action,
    delete_user as delete_user_action,
    generate_password_reset_link as generate_password_reset_link_action,
    update_user as update_user_action,
)
from selfprivacy_api.exceptions import PLEASE_UPDATE_APP_TEXT
from selfprivacy_api.exceptions.abstract_exception import AbstractException
from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.graphql.common_types.user import (
    PasswordResetLinkReturn,
    UserMutationReturn,
    get_user_by_username,
)
from selfprivacy_api.graphql.mutations.mutation_interface import (
    GenericMutationReturn,
)
from selfprivacy_api.utils.localization import (
    TranslateSystemMessage as t,
    get_locale,
)

tracer = trace.get_tracer(__name__)

_ = gettext.gettext

FAILED_TO_SETUP_SSO_PASSWORD_TEXT = _(
    "New password applied an an email password. To use Single Sign On, please update the SelfPrivacy app."
)


async def return_failed_mutation_return(
    message: str,
    code: int = 400,
    username: Optional[str] = None,
) -> UserMutationReturn:
    return UserMutationReturn(
        success=False,
        message=str(message),
        code=code,
        user=await get_user_by_username(username) if username else None,
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
    async def create_user(
        self, user: UserMutationInput, info: Info
    ) -> UserMutationReturn:
        locale = get_locale(info=info)

        with tracer.start_as_current_span(
            "create_user_mutation",
            attributes={
                "username": user.username,
            },
        ):
            try:
                await create_user_action(
                    username=user.username,
                    password=user.password,
                    directmemberof=user.directmemberof,
                    displayname=user.display_name,
                )
            except Exception as error:
                if isinstance(error, AbstractException):
                    return await return_failed_mutation_return(
                        message=error.get_error_message(locale=locale),
                        code=error.code,
                    )
                else:
                    return await return_failed_mutation_return(
                        message=str(error),
                        code=400,
                    )

            if user.password:
                return UserMutationReturn(
                    success=True,
                    message=f"{t.translate(text=FAILED_TO_SETUP_SSO_PASSWORD_TEXT, locale=locale)} {t.translate(text=PLEASE_UPDATE_APP_TEXT, locale=locale)}",
                    code=201,
                    user=await get_user_by_username(user.username),
                )
            return UserMutationReturn(
                success=True,
                message=t.translate(text=_("User created"), locale=locale),
                code=201,
                user=await get_user_by_username(user.username),
            )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def delete_user(self, username: str, info: Info) -> GenericMutationReturn:
        locale = get_locale(info=info)

        with tracer.start_as_current_span(
            "delete_user_mutation",
            attributes={
                "username": username,
            },
        ):
            try:
                await delete_user_action(username)
            except Exception as error:
                if isinstance(error, AbstractException):
                    return GenericMutationReturn(
                        success=False,
                        message=error.get_error_message(locale=locale),
                        code=error.code,
                    )
                else:
                    return GenericMutationReturn(
                        success=False,
                        message=str(error),
                        code=400,
                    )
            return GenericMutationReturn(
                success=True,
                message=t.translate(text=_("User deleted"), locale=locale),
                code=200,
            )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def update_user(
        self, user: UserMutationInput, info: Info
    ) -> UserMutationReturn:
        """Update user mutation"""
        locale = get_locale(info=info)

        with tracer.start_as_current_span(
            "update_user_mutation",
            attributes={
                "username": user.username,
            },
        ):
            try:
                await update_user_action(
                    username=user.username,
                    password=user.password,
                    directmemberof=user.directmemberof,
                    displayname=user.display_name,
                )
            except Exception as error:
                if isinstance(error, AbstractException):
                    return await return_failed_mutation_return(
                        message=error.get_error_message(locale=locale),
                        username=user.username,
                        code=error.code,
                    )
                else:
                    return await return_failed_mutation_return(
                        message=str(error),
                        username=user.username,
                        code=400,
                    )

            if user.password:
                return UserMutationReturn(
                    success=True,
                    message=f"{t.translate(text=_(FAILED_TO_SETUP_SSO_PASSWORD_TEXT), locale=locale)} {t.translate(text=_(PLEASE_UPDATE_APP_TEXT), locale=locale)}",
                    code=200,
                    user=await get_user_by_username(user.username),
                )

            return UserMutationReturn(
                success=True,
                message=t.translate(text=_("User updated"), locale=locale),
                code=200,
                user=await get_user_by_username(user.username),
            )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def add_ssh_key(
        self, ssh_input: SshMutationInput, info: Info
    ) -> UserMutationReturn:
        """Add a new ssh key"""
        locale = get_locale(info=info)

        with tracer.start_as_current_span(
            "add_ssh_key_mutation",
            attributes={
                "username": ssh_input.username,
            },
        ):
            try:
                create_ssh_key_action(ssh_input.username, ssh_input.ssh_key)
            except Exception as error:
                if isinstance(error, AbstractException):
                    return await return_failed_mutation_return(
                        message=error.get_error_message(locale=locale),
                        code=error.code,
                    )
                else:
                    return await return_failed_mutation_return(
                        message=str(error),
                        code=500,
                    )
            return UserMutationReturn(
                success=True,
                message=t.translate(
                    text=_("New SSH key successfully written"), locale=locale
                ),
                code=201,
                user=await get_user_by_username(ssh_input.username),
            )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def remove_ssh_key(
        self, ssh_input: SshMutationInput, info: Info
    ) -> UserMutationReturn:
        """Remove ssh key from user"""
        locale = get_locale(info=info)

        with tracer.start_as_current_span(
            "remove_ssh_key_mutation",
            attributes={
                "username": ssh_input.username,
            },
        ):
            try:
                remove_ssh_key_action(ssh_input.username, ssh_input.ssh_key)
            except Exception as error:
                if isinstance(error, AbstractException):
                    return UserMutationReturn(
                        success=False,
                        message=error.get_error_message(locale=locale),
                        code=error.code,
                    )
                else:
                    return UserMutationReturn(
                        success=False,
                        message=str(error),
                        code=500,
                    )
            return UserMutationReturn(
                success=True,
                message=t.translate(
                    text=_("SSH key successfully removed"), locale=locale
                ),
                code=200,
                user=await get_user_by_username(ssh_input.username),
            )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def generate_password_reset_link(
        self, username: str, info: Info
    ) -> PasswordResetLinkReturn:
        locale = get_locale(info=info)

        with tracer.start_as_current_span(
            "generate_password_reset_link_mutation",
            attributes={
                "username": username,
            },
        ):
            try:
                password_reset_link = await generate_password_reset_link_action(
                    username=username
                )
            except Exception as error:
                if isinstance(error, AbstractException):
                    return PasswordResetLinkReturn(
                        success=False,
                        message=error.get_error_message(locale=locale),
                        code=error.code,
                    )
                else:
                    return PasswordResetLinkReturn(
                        success=False,
                        message=str(error),
                        code=400,
                    )
            return PasswordResetLinkReturn(
                success=True,
                message=t.translate(text=_("Link successfully created"), locale=locale),
                code=200,
                password_reset_link=password_reset_link,
            )
