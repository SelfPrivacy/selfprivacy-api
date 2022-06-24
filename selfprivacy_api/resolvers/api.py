"""Resolvers for API module"""
import datetime
import typing
from flask import request

from selfprivacy_api.graphql.queries.api_fields import ApiDevice, ApiRecoveryKeyStatus

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

def get_devices() -> typing.List[ApiDevice]:
    """Get list of devices"""
    caller_name = get_token_name(request.headers.get("Authorization").split(" ")[1] if request.headers.get("Authorization") is not None else None)
    tokens = get_tokens_info()
    return [
        ApiDevice(
            name=token["name"],
            creation_date=datetime.datetime.strptime(token["date"], "%Y-%m-%dT%H:%M:%S.%fZ"),
            is_caller=token["name"] == caller_name,
        )
        for token in tokens
    ]

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
        creation_date=datetime.datetime.strptime(status["date"], "%Y-%m-%dT%H:%M:%S.%fZ"),
        expiration_date=datetime.datetime.strptime(status["expiration"], "%Y-%m-%dT%H:%M:%S.%fZ") if status["expiration"] is not None else None,
        uses_left=status["uses_left"] if status["uses_left"] is not None else None,
    )
