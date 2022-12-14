"""
Token repository using Redis as backend.
"""
from typing import Optional
from datetime import datetime

from selfprivacy_api.repositories.tokens.abstract_tokens_repository import (
    AbstractTokensRepository,
)
from selfprivacy_api.utils.redis_pool import RedisPool
from selfprivacy_api.models.tokens.token import Token
from selfprivacy_api.models.tokens.recovery_key import RecoveryKey
from selfprivacy_api.models.tokens.new_device_key import NewDeviceKey

TOKENS_PREFIX = "token_repo:tokens:"


class RedisTokensRepository(AbstractTokensRepository):
    """
    Token repository using Redis as a backend
    """

    def __init__(self):
        self.connection = RedisPool().get_connection()

    @staticmethod
    def token_key_for_device(device_name: str):
        return TOKENS_PREFIX + str(hash(device_name))

    def get_tokens(self) -> list[Token]:
        """Get the tokens"""
        r = self.connection
        token_keys = r.keys(TOKENS_PREFIX + "*")
        return [self._token_from_hash(key) for key in token_keys]

    def delete_token(self, input_token: Token) -> None:
        """Delete the token"""
        r = self.connection
        key = RedisTokensRepository._token_redis_key(input_token)
        r.delete(key)

    def get_recovery_key(self) -> Optional[RecoveryKey]:
        """Get the recovery key"""
        raise NotImplementedError

    def create_recovery_key(
        self,
        expiration: Optional[datetime],
        uses_left: Optional[int],
    ) -> RecoveryKey:
        """Create the recovery key"""
        raise NotImplementedError

    def get_new_device_key(self) -> NewDeviceKey:
        """Creates and returns the new device key"""
        raise NotImplementedError

    def delete_new_device_key(self) -> None:
        """Delete the new device key"""
        raise NotImplementedError

    @staticmethod
    def _token_redis_key(token: Token) -> str:
        return RedisTokensRepository.token_key_for_device(token.device_name)

    def _store_token(self, new_token: Token):
        """Store a token directly"""
        key = RedisTokensRepository._token_redis_key(new_token)
        self._store_token_as_hash(key, new_token)

    def _decrement_recovery_token(self):
        """Decrement recovery key use count by one"""
        raise NotImplementedError

    def _get_stored_new_device_key(self) -> Optional[NewDeviceKey]:
        """Retrieves new device key that is already stored."""
        raise NotImplementedError

    def _token_from_hash(self, redis_key: str) -> Token:
        r = self.connection
        if r.exists(redis_key):
            token_dict = r.hgetall(redis_key)
            for date in [
                "created_at",
            ]:
                if token_dict[date] != "None":
                    token_dict[date] = datetime.fromisoformat(token_dict[date])
            for key in token_dict.keys():
                if token_dict[key] == "None":
                    token_dict[key] = None

            return Token(**token_dict)
        return None

    def _store_token_as_hash(self, redis_key, model):
        r = self.connection
        for key, value in model.dict().items():
            if isinstance(value, datetime):
                value = value.isoformat()
            r.hset(redis_key, key, str(value))
