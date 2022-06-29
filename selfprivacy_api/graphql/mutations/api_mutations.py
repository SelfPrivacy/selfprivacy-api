"""API access mutations"""
# pylint: disable=too-few-public-methods
import datetime
import typing
from flask import request
import strawberry
from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.graphql.mutations.mutation_interface import MutationReturnInterface
from selfprivacy_api.utils import parse_date

from selfprivacy_api.utils.auth import (
    generate_recovery_token
)

@strawberry.type
class ApiKeyMutationReturn(MutationReturnInterface):
    key: typing.Optional[str]

@strawberry.input
class RecoveryKeyLimitsInput:
    """Recovery key limits input"""
    expiration_date: typing.Optional[datetime.datetime]
    uses: typing.Optional[int]

@strawberry.type
class ApiMutations:
    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def getNewRecoveryApiKey(self, limits: RecoveryKeyLimitsInput) -> ApiKeyMutationReturn:
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
