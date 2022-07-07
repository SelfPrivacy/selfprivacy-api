"""API access mutations"""
# pylint: disable=too-few-public-methods
import datetime
import typing
from flask import request
import strawberry
from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.graphql.mutations.mutation_interface import (
    GenericMutationReturn,
    MutationReturnInterface,
)

from selfprivacy_api.utils.auth import (
    delete_new_device_auth_token,
    delete_token,
    generate_recovery_token,
    get_new_device_auth_token,
    is_token_name_exists,
    is_token_name_pair_valid,
    refresh_token,
    use_mnemonic_recoverery_token,
    use_new_device_auth_token,
)


@strawberry.type
class ApiKeyMutationReturn(MutationReturnInterface):
    key: typing.Optional[str]


@strawberry.type
class DeviceApiTokenMutationReturn(MutationReturnInterface):
    token: typing.Optional[str]


@strawberry.input
class RecoveryKeyLimitsInput:
    """Recovery key limits input"""

    expiration_date: typing.Optional[datetime.datetime]
    uses: typing.Optional[int]


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
        self, limits: RecoveryKeyLimitsInput
    ) -> ApiKeyMutationReturn:
        """Generate recovery key"""
        if limits.expiration_date is not None:
            if limits.expiration_date < datetime.datetime.now():
                return ApiKeyMutationReturn(
                    success=False,
                    message="Expiration date must be in the future",
                    code=400,
                    key=None,
                )
        if limits.uses is not None:
            if limits.uses < 1:
                return ApiKeyMutationReturn(
                    success=False,
                    message="Uses must be greater than 0",
                    code=400,
                    key=None,
                )
        key = generate_recovery_token(limits.expiration_date, limits.uses)
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
        token = use_mnemonic_recoverery_token(input.key, input.deviceName)
        if token is None:
            return DeviceApiTokenMutationReturn(
                success=False,
                message="Recovery key not found",
                code=404,
                token=None,
            )
        return DeviceApiTokenMutationReturn(
            success=True,
            message="Recovery key used",
            code=200,
            token=token,
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def refresh_device_api_token(self) -> DeviceApiTokenMutationReturn:
        """Refresh device api token"""
        token = (
            request.headers.get("Authorization").split(" ")[1]
            if request.headers.get("Authorization") is not None
            else None
        )
        if token is None:
            return DeviceApiTokenMutationReturn(
                success=False,
                message="Token not found",
                code=404,
                token=None,
            )
        new_token = refresh_token(token)
        if new_token is None:
            return DeviceApiTokenMutationReturn(
                success=False,
                message="Token not found",
                code=404,
                token=None,
            )
        return DeviceApiTokenMutationReturn(
            success=True,
            message="Token refreshed",
            code=200,
            token=new_token,
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def delete_device_api_token(self, device: str) -> GenericMutationReturn:
        """Delete device api token"""
        self_token = (
            request.headers.get("Authorization").split(" ")[1]
            if request.headers.get("Authorization") is not None
            else None
        )
        if self_token is not None and is_token_name_pair_valid(device, self_token):
            return GenericMutationReturn(
                success=False,
                message="Cannot delete caller's token",
                code=400,
            )
        if not is_token_name_exists(device):
            return GenericMutationReturn(
                success=False,
                message="Token not found",
                code=404,
            )
        delete_token(device)
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
