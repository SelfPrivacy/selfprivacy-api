"""API access mutations"""

# pylint: disable=too-few-public-methods

import gettext
import datetime
from typing import Optional

import strawberry
from strawberry.types import Info

from selfprivacy_api.actions.api_tokens import (
    CannotDeleteCallerException,
    InvalidExpirationDate,
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
from selfprivacy_api.utils.localization import TranslateSystemMessage as t

_ = gettext.gettext


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

        locale = info.context["locale"]
        if limits is None:
            limits = RecoveryKeyLimitsInput()
        try:
            key = get_new_api_recovery_key(limits.expiration_date, limits.uses)
        except InvalidExpirationDate as error:
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

        locale = info.context["locale"]
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

        locale = info.context["locale"]
        token_string = (
            info.context["request"]
            .headers.get("Authorization", "")
            .replace("Bearer ", "")
        )
        if token_string is None:
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

        locale = info.context["locale"]
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

        locale = info.context["locale"]
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

        locale = info.context["locale"]
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

        locale = info.context["locale"]
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
