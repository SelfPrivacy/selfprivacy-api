"""API access status"""
# pylint: disable=too-few-public-methods
import datetime
import typing
from flask import request
import strawberry
from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.utils import parse_date

from selfprivacy_api.utils.auth import (
    get_recovery_token_status,
    get_tokens_info,
    is_recovery_token_exists,
    is_recovery_token_valid,
    is_token_name_exists,
    is_token_name_pair_valid,
    refresh_token,
    get_token_name,
)

def get_api_version() -> str:
    """Get API version"""
    return "1.2.7"

@strawberry.type
class ApiDevice:
    """A single device with SelfPrivacy app installed"""
    name: str
    creation_date: datetime.datetime
    is_caller: bool

def get_devices() -> typing.List[ApiDevice]:
    """Get list of devices"""
    caller_name = get_token_name(request.headers.get("Authorization").split(" ")[1] if request.headers.get("Authorization") is not None else None)
    tokens = get_tokens_info()
    return [
        ApiDevice(
            name=token["name"],
            creation_date=parse_date(token["date"]),
            is_caller=token["name"] == caller_name,
        )
        for token in tokens
    ]


@strawberry.type
class ApiRecoveryKeyStatus:
    """Recovery key status"""
    exists: bool
    valid: bool
    creation_date: typing.Optional[datetime.datetime]
    expiration_date: typing.Optional[datetime.datetime]
    uses_left: typing.Optional[int]

def get_recovery_key_status() -> ApiRecoveryKeyStatus:
    """Get recovery key status"""
    if not is_recovery_token_exists():
        return ApiRecoveryKeyStatus(
            exists=False, valid=False, creation_date=None, expiration_date=None, uses_left=None
        )
    status = get_recovery_token_status()
    if status is None:
        return ApiRecoveryKeyStatus(
            exists=False, valid=False, creation_date=None, expiration_date=None, uses_left=None
        )
    return ApiRecoveryKeyStatus(
        exists=True,
        valid=is_recovery_token_valid(),
        creation_date=parse_date(status["date"]),
        expiration_date=parse_date(status["expiration"]) if status["expiration"] is not None else None,
        uses_left=status["uses_left"] if status["uses_left"] is not None else None,
    )

@strawberry.type
class Api:
    """API access status"""
    version: str = strawberry.field(resolver=get_api_version)
    devices: typing.List[ApiDevice] = strawberry.field(resolver=get_devices, permission_classes=[IsAuthenticated])
    recovery_key: ApiRecoveryKeyStatus = strawberry.field(resolver=get_recovery_key_status, permission_classes=[IsAuthenticated])
