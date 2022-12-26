"""API access mutations"""
# pylint: disable=too-few-public-methods
import datetime
import typing
import strawberry
from strawberry.types import Info
from selfprivacy_api.actions.api_tokens import (
    CannotDeleteCallerException,
    InvalidExpirationDate,
    InvalidUsesLeft,
    NotFoundException,
    delete_api_token,
    get_new_api_recovery_key,
    refresh_api_token,
    delete_new_device_auth_token,
)
from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.graphql.mutations.mutation_interface import (
    GenericMutationReturn,
    MutationReturnInterface,
)

from selfprivacy_api.utils.auth import (
    get_new_device_auth_token,
    use_new_device_auth_token,
)

from selfprivacy_api.repositories.tokens.json_tokens_repository import (
    JsonTokensRepository,
)
from selfprivacy_api.repositories.tokens.exceptions import (
    RecoveryKeyNotFound,
    InvalidMnemonic,
)

TOKEN_REPO = JsonTokensRepository()


@strawberry.type
class ApiKeyMutationReturn(MutationReturnInterface):
    key: typing.Optional[str]


@strawberry.type
class DeviceApiTokenMutationReturn(MutationReturnInterface):
    token: typing.Optional[str]


@strawberry.input
class RecoveryKeyLimitsInput:
    """Recovery key limits input"""

    expiration_date: typing.Optional[datetime.datetime] = None
    uses: typing.Optional[int] = None


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
        self, limits: typing.Optional[RecoveryKeyLimitsInput] = None
    ) -> ApiKeyMutationReturn:
        """Generate recovery key"""
        if limits is None:
            limits = RecoveryKeyLimitsInput()
        try:
            key = get_new_api_recovery_key(limits.expiration_date, limits.uses)
        except InvalidExpirationDate:
            return ApiKeyMutationReturn(
                success=False,
                message="Expiration date must be in the future",
                code=400,
                key=None,
            )
        except InvalidUsesLeft:
            return ApiKeyMutationReturn(
                success=False,
                message="Uses must be greater than 0",
                code=400,
                key=None,
            )
        return ApiKeyMutationReturn(
            success=True,
            message="Recovery key generated",
            code=200,
            key=key,
        )

    @strawberry.mutation()
    def use_recovery_api_key(
        self, input: UseRecoveryKeyInput
    ) -> DeviceApiTokenMutationReturn:
        """Use recovery key"""
        try:
            token = TOKEN_REPO.use_mnemonic_recovery_key(input.key, input.deviceName)
            return DeviceApiTokenMutationReturn(
                success=True,
                message="Recovery key used",
                code=200,
                token=token.token,
            )
        except (RecoveryKeyNotFound, InvalidMnemonic):
            return DeviceApiTokenMutationReturn(
                success=False,
                message="Recovery key not found",
                code=404,
                token=None,
            )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def refresh_device_api_token(self, info: Info) -> DeviceApiTokenMutationReturn:
        """Refresh device api token"""
        token_string = (
            info.context["request"]
            .headers.get("Authorization", "")
            .replace("Bearer ", "")
        )
        if token_string is None:
            return DeviceApiTokenMutationReturn(
                success=False,
                message="Token not found",
                code=404,
                token=None,
            )

        try:
            new_token = refresh_api_token(token_string)
            return DeviceApiTokenMutationReturn(
                success=True,
                message="Token refreshed",
                code=200,
                token=new_token,
            )
        except NotFoundException:
            return DeviceApiTokenMutationReturn(
                success=False,
                message="Token not found",
                code=404,
                token=None,
            )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def delete_device_api_token(self, device: str, info: Info) -> GenericMutationReturn:
        """Delete device api token"""
        self_token = (
            info.context["request"]
            .headers.get("Authorization", "")
            .replace("Bearer ", "")
        )
        try:
            delete_api_token(self_token, device)
        except NotFoundException:
            return GenericMutationReturn(
                success=False,
                message="Token not found",
                code=404,
            )
        except CannotDeleteCallerException:
            return GenericMutationReturn(
                success=False,
                message="Cannot delete caller token",
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
            message="Token deleted",
            code=200,
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def get_new_device_api_key(self) -> ApiKeyMutationReturn:
        """Generate device api key"""
        key = get_new_device_auth_token()
        return ApiKeyMutationReturn(
            success=True,
            message="Device api key generated",
            code=200,
            key=key,
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def invalidate_new_device_api_key(self) -> GenericMutationReturn:
        """Invalidate new device api key"""
        delete_new_device_auth_token()
        return GenericMutationReturn(
            success=True,
            message="New device key deleted",
            code=200,
        )

    @strawberry.mutation()
    def authorize_with_new_device_api_key(
        self, input: UseNewDeviceKeyInput
    ) -> DeviceApiTokenMutationReturn:
        """Authorize with new device api key"""
        token = use_new_device_auth_token(input.key, input.deviceName)
        if token is None:
            return DeviceApiTokenMutationReturn(
                success=False,
                message="Token not found",
                code=404,
                token=None,
            )
        return DeviceApiTokenMutationReturn(
            success=True,
            message="Token used",
            code=200,
            token=token,
        )
