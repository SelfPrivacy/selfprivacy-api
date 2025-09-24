"""
App tokens actions.
The only actions on tokens that are accessible from APIs
"""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel
from mnemonic import Mnemonic
from opentelemetry import trace

from selfprivacy_api.utils.timeutils import ensure_tz_aware, ensure_tz_aware_strict
from selfprivacy_api.repositories.tokens import ACTIVE_TOKEN_PROVIDER
from selfprivacy_api.repositories.tokens.exceptions import (
    TokenNotFound,
    RecoveryKeyNotFound,
    InvalidMnemonic,
    NewDeviceKeyNotFound,
)

tracer = trace.get_tracer(__name__)


class TokenInfoWithIsCaller(BaseModel):
    """Token info"""

    name: str
    date: datetime
    is_caller: bool


def _naive(date_time: datetime) -> datetime:
    if date_time is None:
        return None
    if date_time.tzinfo is not None:
        date_time.astimezone(timezone.utc)
    return date_time.replace(tzinfo=None)


@tracer.start_as_current_span("get_api_tokens_with_caller_flag")
def get_api_tokens_with_caller_flag(caller_token: str) -> list[TokenInfoWithIsCaller]:
    """Get the tokens info"""
    caller_name = ACTIVE_TOKEN_PROVIDER.get_token_by_token_string(
        caller_token
    ).device_name
    tokens = ACTIVE_TOKEN_PROVIDER.get_tokens()
    return [
        TokenInfoWithIsCaller(
            name=token.device_name,
            date=token.created_at,
            is_caller=token.device_name == caller_name,
        )
        for token in tokens
    ]


@tracer.start_as_current_span("is_token_valid")
def is_token_valid(token) -> bool:
    """Check if token is valid"""
    return ACTIVE_TOKEN_PROVIDER.is_token_valid(token)


class NotFoundException(Exception):
    """Not found exception"""


class CannotDeleteCallerException(Exception):
    """Cannot delete caller exception"""


@tracer.start_as_current_span("create_api_token")
def delete_api_token(caller_token: str, token_name: str) -> None:
    """Delete the token"""
    if ACTIVE_TOKEN_PROVIDER.is_token_name_pair_valid(token_name, caller_token):
        raise CannotDeleteCallerException("Cannot delete caller's token")
    if not ACTIVE_TOKEN_PROVIDER.is_token_name_exists(token_name):
        raise NotFoundException("Token not found")
    token = ACTIVE_TOKEN_PROVIDER.get_token_by_name(token_name)
    ACTIVE_TOKEN_PROVIDER.delete_token(token)


@tracer.start_as_current_span("create_api_token")
def refresh_api_token(caller_token: str) -> str:
    """Refresh the token"""
    try:
        old_token = ACTIVE_TOKEN_PROVIDER.get_token_by_token_string(caller_token)
        new_token = ACTIVE_TOKEN_PROVIDER.refresh_token(old_token)
    except TokenNotFound:
        raise NotFoundException("Token not found")
    return new_token.token


class RecoveryTokenStatus(BaseModel):
    """Recovery token status"""

    exists: bool
    valid: bool
    date: Optional[datetime] = None
    expiration: Optional[datetime] = None
    uses_left: Optional[int] = None


@tracer.start_as_current_span("get_api_recovery_token_status")
def get_api_recovery_token_status() -> RecoveryTokenStatus:
    """Get the recovery token status, timezone-aware"""
    token = ACTIVE_TOKEN_PROVIDER.get_recovery_key()
    if token is None:
        return RecoveryTokenStatus(exists=False, valid=False)
    is_valid = ACTIVE_TOKEN_PROVIDER.is_recovery_key_valid()

    # New tokens are tz-aware, but older ones might not be
    expiry_date = token.expires_at
    if expiry_date is not None:
        expiry_date = ensure_tz_aware_strict(expiry_date)

    return RecoveryTokenStatus(
        exists=True,
        valid=is_valid,
        date=ensure_tz_aware_strict(token.created_at),
        expiration=expiry_date,
        uses_left=token.uses_left,
    )


class InvalidExpirationDate(Exception):
    """Invalid expiration date exception"""


class InvalidUsesLeft(Exception):
    """Invalid uses left exception"""


@tracer.start_as_current_span("get_new_api_recovery_key")
def get_new_api_recovery_key(
    expiration_date: Optional[datetime] = None, uses_left: Optional[int] = None
) -> str:
    """Get new recovery key"""
    if expiration_date is not None:
        expiration_date = ensure_tz_aware(expiration_date)
        current_time = datetime.now(timezone.utc)
        if expiration_date < current_time:
            raise InvalidExpirationDate("Expiration date is in the past")
    if uses_left is not None:
        if uses_left <= 0:
            raise InvalidUsesLeft("Uses must be greater than 0")

    key = ACTIVE_TOKEN_PROVIDER.create_recovery_key(expiration_date, uses_left)
    mnemonic_phrase = Mnemonic(language="english").to_mnemonic(bytes.fromhex(key.key))
    return mnemonic_phrase


@tracer.start_as_current_span("use_mnemonic_recovery_token")
def use_mnemonic_recovery_token(mnemonic_phrase, name):
    """Use the recovery token by converting the mnemonic word list to a byte array.
    If the recovery token if invalid itself, return None
    If the binary representation of phrase not matches
    the byte array of the recovery token, return None.
    If the mnemonic phrase is valid then generate a device token and return it.
    Substract 1 from uses_left if it exists.
    mnemonic_phrase is a string representation of the mnemonic word list.
    """
    try:
        token = ACTIVE_TOKEN_PROVIDER.use_mnemonic_recovery_key(mnemonic_phrase, name)
        return token.token
    except (RecoveryKeyNotFound, InvalidMnemonic):
        return None


@tracer.start_as_current_span("delete_new_device_auth_token")
def delete_new_device_auth_token() -> None:
    ACTIVE_TOKEN_PROVIDER.delete_new_device_key()


@tracer.start_as_current_span("get_new_device_auth_token")
def get_new_device_auth_token() -> str:
    """Generate and store a new device auth token which is valid for 10 minutes
    and return a mnemonic phrase representation
    """
    key = ACTIVE_TOKEN_PROVIDER.get_new_device_key()
    return Mnemonic(language="english").to_mnemonic(bytes.fromhex(key.key))


@tracer.start_as_current_span("use_new_device_auth_token")
def use_new_device_auth_token(mnemonic_phrase, name) -> Optional[str]:
    """Use the new device auth token by converting the mnemonic string to a byte array.
    If the mnemonic phrase is valid then generate a device token and return it.
    New device auth token must be deleted.
    """
    try:
        token = ACTIVE_TOKEN_PROVIDER.use_mnemonic_new_device_key(mnemonic_phrase, name)
        return token.token
    except (NewDeviceKeyNotFound, InvalidMnemonic):
        return None
