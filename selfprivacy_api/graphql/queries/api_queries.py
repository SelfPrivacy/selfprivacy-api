"""API access status"""

# pylint: disable=too-few-public-methods

import datetime
import typing

import strawberry
from opentelemetry import trace
from strawberry.types import Info

from selfprivacy_api.actions.api_tokens import (
    get_api_recovery_token_status,
    get_api_tokens_with_caller_flag,
)
from selfprivacy_api.dependencies import get_api_version as get_api_version_dependency
from selfprivacy_api.graphql import IsAuthenticated

tracer = trace.get_tracer(__name__)


@tracer.start_as_current_span("resolve_get_api_version")
async def get_api_version() -> str:
    """Get API version"""
    return get_api_version_dependency()


@strawberry.type
class ApiDevice:
    """A single device with SelfPrivacy app installed"""

    name: str
    creation_date: datetime.datetime
    is_caller: bool


@strawberry.type
class ApiRecoveryKeyStatus:
    """Recovery key status"""

    exists: bool
    valid: bool
    creation_date: typing.Optional[datetime.datetime]
    expiration_date: typing.Optional[datetime.datetime]
    uses_left: typing.Optional[int]


@tracer.start_as_current_span("resolve_get_recovery_key_status")
async def get_recovery_key_status() -> ApiRecoveryKeyStatus:
    """Get recovery key status, times are timezone-aware"""
    status = get_api_recovery_token_status()
    if status is None or not status.exists:
        return ApiRecoveryKeyStatus(
            exists=False,
            valid=False,
            creation_date=None,
            expiration_date=None,
            uses_left=None,
        )
    return ApiRecoveryKeyStatus(
        exists=True,
        valid=status.valid,
        creation_date=status.date,
        expiration_date=status.expiration,
        uses_left=status.uses_left,
    )


@strawberry.type
class Api:
    """API access status"""

    version: str = strawberry.field(resolver=get_api_version)

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def devices(self, info: Info) -> typing.List[ApiDevice]:
        with tracer.start_as_current_span("resolve_api_devices"):
            return [
                ApiDevice(
                    name=device.name,
                    creation_date=device.date,
                    is_caller=device.is_caller,
                )
                for device in get_api_tokens_with_caller_flag(
                    info.context["request"]
                    .headers.get("Authorization", "")
                    .replace("Bearer ", "")
                )
            ]

    recovery_key: ApiRecoveryKeyStatus = strawberry.field(
        resolver=get_recovery_key_status, permission_classes=[IsAuthenticated]
    )
