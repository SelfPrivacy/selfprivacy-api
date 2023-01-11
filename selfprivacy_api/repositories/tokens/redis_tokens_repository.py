"""
Token repository using Redis as backend.
"""
from typing import Optional
from datetime import datetime, timezone

from selfprivacy_api.repositories.tokens.abstract_tokens_repository import (
    AbstractTokensRepository,
)
from selfprivacy_api.utils.redis_pool import RedisPool
from selfprivacy_api.models.tokens.token import Token
from selfprivacy_api.models.tokens.recovery_key import RecoveryKey
from selfprivacy_api.models.tokens.new_device_key import NewDeviceKey
from selfprivacy_api.repositories.tokens.exceptions import TokenNotFound

TOKENS_PREFIX = "token_repo:tokens:"
NEW_DEVICE_KEY_REDIS_KEY = "token_repo:new_device_key"
RECOVERY_KEY_REDIS_KEY = "token_repo:recovery_key"


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
        redis = self.connection
        token_keys = redis.keys(TOKENS_PREFIX + "*")
        tokens = []
        for key in token_keys:
            token = self._token_from_hash(key)
            if token is not None:
                # token creation dates are temporarily not tz-aware
                token.created_at = token.created_at.replace(tzinfo=None)
                tokens.append(token)
        return tokens

    def delete_token(self, input_token: Token) -> None:
        """Delete the token"""
        redis = self.connection
        key = RedisTokensRepository._token_redis_key(input_token)
        if input_token not in self.get_tokens():
            raise TokenNotFound
        redis.delete(key)

    def reset(self):
        for token in self.get_tokens():
            self.delete_token(token)
        self.delete_new_device_key()
        redis = self.connection
        redis.delete(RECOVERY_KEY_REDIS_KEY)

    def get_recovery_key(self) -> Optional[RecoveryKey]:
        """Get the recovery key"""
        redis = self.connection
        if redis.exists(RECOVERY_KEY_REDIS_KEY):
            return self._recovery_key_from_hash(RECOVERY_KEY_REDIS_KEY)
        return None

    def create_recovery_key(
        self,
        expiration: Optional[datetime],
        uses_left: Optional[int],
    ) -> RecoveryKey:
        """Create the recovery key"""
        recovery_key = RecoveryKey.generate(expiration=expiration, uses_left=uses_left)
        self._store_model_as_hash(RECOVERY_KEY_REDIS_KEY, recovery_key)
        return recovery_key

    def _store_new_device_key(self, new_device_key: NewDeviceKey) -> None:
        """Store new device key directly"""
        self._store_model_as_hash(NEW_DEVICE_KEY_REDIS_KEY, new_device_key)

    def delete_new_device_key(self) -> None:
        """Delete the new device key"""
        redis = self.connection
        redis.delete(NEW_DEVICE_KEY_REDIS_KEY)

    @staticmethod
    def _token_redis_key(token: Token) -> str:
        return RedisTokensRepository.token_key_for_device(token.device_name)

    def _store_token(self, new_token: Token):
        """Store a token directly"""
        key = RedisTokensRepository._token_redis_key(new_token)
        self._store_model_as_hash(key, new_token)

    def _decrement_recovery_token(self):
        """Decrement recovery key use count by one"""
        if self.is_recovery_key_valid():
            recovery_key = self.get_recovery_key()
            if recovery_key is None:
                return
            uses_left = recovery_key.uses_left
            if uses_left is not None:
                redis = self.connection
                redis.hset(RECOVERY_KEY_REDIS_KEY, "uses_left", uses_left - 1)

    def _get_stored_new_device_key(self) -> Optional[NewDeviceKey]:
        """Retrieves new device key that is already stored."""
        return self._new_device_key_from_hash(NEW_DEVICE_KEY_REDIS_KEY)

    @staticmethod
    def _is_date_key(key: str):
        return key in [
            "created_at",
            "expires_at",
        ]

    @staticmethod
    def _prepare_model_dict(d: dict):
        date_keys = [key for key in d.keys() if RedisTokensRepository._is_date_key(key)]
        for date in date_keys:
            if d[date] != "None":
                d[date] = datetime.fromisoformat(d[date])
        for key in d.keys():
            if d[key] == "None":
                d[key] = None

    def _model_dict_from_hash(self, redis_key: str) -> Optional[dict]:
        redis = self.connection
        if redis.exists(redis_key):
            token_dict = redis.hgetall(redis_key)
            RedisTokensRepository._prepare_model_dict(token_dict)
            return token_dict
        return None

    def _hash_as_model(self, redis_key: str, model_class):
        token_dict = self._model_dict_from_hash(redis_key)
        if token_dict is not None:
            return model_class(**token_dict)
        return None

    def _token_from_hash(self, redis_key: str) -> Optional[Token]:
        return self._hash_as_model(redis_key, Token)

    def _recovery_key_from_hash(self, redis_key: str) -> Optional[RecoveryKey]:
        return self._hash_as_model(redis_key, RecoveryKey)

    def _new_device_key_from_hash(self, redis_key: str) -> Optional[NewDeviceKey]:
        return self._hash_as_model(redis_key, NewDeviceKey)

    def _store_model_as_hash(self, redis_key, model):
        redis = self.connection
        for key, value in model.dict().items():
            if isinstance(value, datetime):
                if value.tzinfo is None:
                    value = value.replace(tzinfo=timezone.utc)
                value = value.isoformat()
            redis.hset(redis_key, key, str(value))
