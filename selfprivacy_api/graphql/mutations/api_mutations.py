"""API access mutations"""

# pylint: disable=too-few-public-methods

import gettext
import datetime
from typing import Optional

import strawberry
from opentelemetry import trace
from strawberry.types import Info

from selfprivacy_api.actions.api_tokens import (
    CannotDeleteCallerException,
    ExpirationDateInThePast,
    InvalidUsesLeft,
    delete_api_token,
    get_new_api_recovery_key,
    use_mnemonic_recovery_token,
    refresh_api_token,
    delete_new_device_auth_token,
    get_new_device_auth_token,
    use_new_device_auth_token,
)
from selfprivacy_api.repositories.tokens.exceptions import (
    TokenNotFound,
    RecoveryKeyNotFound,
)
from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.graphql.mutations.mutation_interface import (
    GenericMutationReturn,
    MutationReturnInterface,
)
from selfprivacy_api.utils.localization import (
    TranslateSystemMessage as t,
    get_locale,
)

_ = gettext.gettext

tracer = trace.get_tracer(__name__)


@strawberry.type
class ApiKeyMutationReturn(MutationReturnInterface):
    key: Optional[str]


@strawberry.type
class DeviceApiTokenMutationReturn(MutationReturnInterface):
    token: Optional[str]


@strawberry.input
class RecoveryKeyLimitsInput:
    """Recovery key limits input"""

    expiration_date: Optional[datetime.datetime] = None
    uses: Optional[int] = None


@strawberry.input
class UseRecoveryKeyInput:
    """Use recovery key input"""

    key: str
    deviceName: str


@strawberry.input
class UseNewDeviceKeyInput:
    """Use new device key input"""

    key: str
    deviceName: str


@strawberry.type
class ApiMutations:
    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def get_new_recovery_api_key(
        self,
        info: Info,
        limits: Optional[RecoveryKeyLimitsInput] = None,
    ) -> ApiKeyMutationReturn:
        """Generate recovery key"""
        locale = get_locale(info=info)

        with tracer.start_as_current_span(
            "get_new_recovery_api_key",
            attributes={
                "expiration_date": str(
                    limits.expiration_date
                    if limits and limits.expiration_date
                    else "None"
                ),
                "uses": limits.uses if limits and limits.uses else "None",
            },
        ):
            if limits is None:
                limits = RecoveryKeyLimitsInput()
            try:
                key = get_new_api_recovery_key(limits.expiration_date, limits.uses)

            except ExpirationDateInThePast as error:
                return ApiKeyMutationReturn(
                    success=False,
                    message=error.get_error_message(locale=locale),
                    code=400,
                    key=None,
                )
            except InvalidUsesLeft as error:
                return ApiKeyMutationReturn(
                    success=False,
                    message=error.get_error_message(locale=locale),
                    code=400,
                    key=None,
                )
            return ApiKeyMutationReturn(
                success=True,
                message=t.translate(text=_("Recovery key generated"), locale=locale),
                code=200,
                key=key,
            )

    @strawberry.mutation()
    def use_recovery_api_key(
        self, input: UseRecoveryKeyInput, info: Info
    ) -> DeviceApiTokenMutationReturn:
        """Use recovery key"""
        locale = get_locale(info=info)

        with tracer.start_as_current_span(
            "use_recovery_api_key",
            attributes={
                "device_name": input.deviceName,
            },
        ):
            token = use_mnemonic_recovery_token(input.key, input.deviceName)
            if token is not None:
                return DeviceApiTokenMutationReturn(
                    success=True,
                    message=t.translate(text=_("Recovery key used"), locale=locale),
                    code=200,
                    token=token,
                )
            else:
                return DeviceApiTokenMutationReturn(
                    success=False,
                    message=RecoveryKeyNotFound.get_error_message(locale=locale),
                    code=404,
                    token=None,
                )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def refresh_device_api_token(self, info: Info) -> DeviceApiTokenMutationReturn:
        """Refresh device api token"""
        locale = get_locale(info=info)

        with tracer.start_as_current_span("refresh_device_api_token"):
            token_string = (
                info.context["request"]
                .headers.get("Authorization", "")
                .replace("Bearer ", "")
            )
            if not token_string:
                return DeviceApiTokenMutationReturn(
                    success=False,
                    message=TokenNotFound.get_error_message(locale=locale),
                    code=404,
                    token=None,
                )

            try:
                new_token = refresh_api_token(token_string)
                return DeviceApiTokenMutationReturn(
                    success=True,
                    message=t.translate(text=_("Token refreshed"), locale=locale),
                    code=200,
                    token=new_token,
                )
            except TokenNotFound as error:
                return DeviceApiTokenMutationReturn(
                    success=False,
                    message=error.get_error_message(locale=locale),
                    code=404,
                    token=None,
                )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def delete_device_api_token(self, device: str, info: Info) -> GenericMutationReturn:
        """Delete device api token"""
        locale = get_locale(info=info)

        with tracer.start_as_current_span(
            "delete_device_api_token",
            attributes={
                "device": device,
            },
        ):
            self_token = (
                info.context["request"]
                .headers.get("Authorization", "")
                .replace("Bearer ", "")
            )
            try:
                delete_api_token(self_token, device)
            except TokenNotFound as error:
                return GenericMutationReturn(
                    success=False,
                    message=error.get_error_message(locale=locale),
                    code=404,
                )
            except CannotDeleteCallerException as error:
                return GenericMutationReturn(
                    success=False,
                    message=error.get_error_message(locale=locale),
                    code=400,
                )
            except Exception as e:
                return GenericMutationReturn(
                    success=False,
                    message=str(e),
                    code=500,
                )
            return GenericMutationReturn(
                success=True,
                message=t.translate(text=_("Token deleted"), locale=locale),
                code=200,
            )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def get_new_device_api_key(self, info: Info) -> ApiKeyMutationReturn:
        """Generate device api key"""
        locale = get_locale(info=info)

        with tracer.start_as_current_span("get_new_device_api_key"):
            key = get_new_device_auth_token()
            return ApiKeyMutationReturn(
                success=True,
                message=t.translate(text=_("Device api key generated"), locale=locale),
                code=200,
                key=key,
            )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def invalidate_new_device_api_key(self, info: Info) -> GenericMutationReturn:
        """Invalidate new device api key"""
        locale = get_locale(info=info)

        with tracer.start_as_current_span("invalidate_new_device_api_key"):
            delete_new_device_auth_token()
            return GenericMutationReturn(
                success=True,
                message=t.translate(text=_("New device key deleted"), locale=locale),
                code=200,
            )

    @strawberry.mutation()
    def authorize_with_new_device_api_key(
        self, input: UseNewDeviceKeyInput, info: Info
    ) -> DeviceApiTokenMutationReturn:
        """Authorize with new device api key"""
        locale = get_locale(info=info)

        with tracer.start_as_current_span(
            "authorize_with_new_device_api_key",
            attributes={
                "device_name": input.deviceName,
            },
        ):
            token = use_new_device_auth_token(input.key, input.deviceName)
            if token is None:
                return DeviceApiTokenMutationReturn(
                    success=False,
                    message=TokenNotFound.get_error_message(locale=locale),
                    code=404,
                    token=None,
                )
            return DeviceApiTokenMutationReturn(
                success=True,
                message=t.translate(text=_("Token used"), locale=locale),
                code=200,
                token=token,
            )
