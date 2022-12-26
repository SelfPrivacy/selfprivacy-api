"""App tokens actions"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from mnemonic import Mnemonic

from selfprivacy_api.repositories.tokens.json_tokens_repository import (
    JsonTokensRepository,
)
from selfprivacy_api.repositories.tokens.exceptions import TokenNotFound

TOKEN_REPO = JsonTokensRepository()


class TokenInfoWithIsCaller(BaseModel):
    """Token info"""

    name: str
    date: datetime
    is_caller: bool


def get_api_tokens_with_caller_flag(caller_token: str) -> list[TokenInfoWithIsCaller]:
    """Get the tokens info"""
    caller_name = TOKEN_REPO.get_token_by_token_string(caller_token).device_name
    tokens = TOKEN_REPO.get_tokens()
    return [
        TokenInfoWithIsCaller(
            name=token.device_name,
            date=token.created_at,
            is_caller=token.device_name == caller_name,
        )
        for token in tokens
    ]


class NotFoundException(Exception):
    """Not found exception"""


class CannotDeleteCallerException(Exception):
    """Cannot delete caller exception"""


def delete_api_token(caller_token: str, token_name: str) -> None:
    """Delete the token"""
    if TOKEN_REPO.is_token_name_pair_valid(token_name, caller_token):
        raise CannotDeleteCallerException("Cannot delete caller's token")
    if not TOKEN_REPO.is_token_name_exists(token_name):
        raise NotFoundException("Token not found")
    token = TOKEN_REPO.get_token_by_name(token_name)
    TOKEN_REPO.delete_token(token)


def refresh_api_token(caller_token: str) -> str:
    """Refresh the token"""
    try:
        old_token = TOKEN_REPO.get_token_by_token_string(caller_token)
        new_token = TOKEN_REPO.refresh_token(old_token)
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


def get_api_recovery_token_status() -> RecoveryTokenStatus:
    """Get the recovery token status"""
    token = TOKEN_REPO.get_recovery_key()
    if token is None:
        return RecoveryTokenStatus(exists=False, valid=False)
    is_valid = TOKEN_REPO.is_recovery_key_valid()
    return RecoveryTokenStatus(
        exists=True,
        valid=is_valid,
        date=token.created_at,
        expiration=token.expires_at,
        uses_left=token.uses_left,
    )


class InvalidExpirationDate(Exception):
    """Invalid expiration date exception"""


class InvalidUsesLeft(Exception):
    """Invalid uses left exception"""


def get_new_api_recovery_key(
    expiration_date: Optional[datetime] = None, uses_left: Optional[int] = None
) -> str:
    """Get new recovery key"""
    if expiration_date is not None:
        current_time = datetime.now().timestamp()
        if expiration_date.timestamp() < current_time:
            raise InvalidExpirationDate("Expiration date is in the past")
    if uses_left is not None:
        if uses_left <= 0:
            raise InvalidUsesLeft("Uses must be greater than 0")

    key = TOKEN_REPO.create_recovery_key(expiration_date, uses_left)
    mnemonic_phrase = Mnemonic(language="english").to_mnemonic(bytes.fromhex(key.key))
    return mnemonic_phrase


def delete_new_device_auth_token() -> None:
    TOKEN_REPO.delete_new_device_key()
