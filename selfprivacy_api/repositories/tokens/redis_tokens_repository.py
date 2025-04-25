"""
Token repository using Redis as backend.
"""

from typing import Any, Optional
from datetime import datetime, timezone
from hashlib import md5

from selfprivacy_api.utils.redis_pool import RedisPool

from selfprivacy_api.models.tokens.token import Token
from selfprivacy_api.models.tokens.recovery_key import RecoveryKey
from selfprivacy_api.models.tokens.new_device_key import NewDeviceKey

from selfprivacy_api.repositories.tokens.exceptions import TokenNotFound
from selfprivacy_api.repositories.tokens.abstract_tokens_repository import (
    AbstractTokensRepository,
)

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
        md5_hash = md5(usedforsecurity=False)
        md5_hash.update(bytes(device_name, "utf-8"))
        digest = md5_hash.hexdigest()
        return TOKENS_PREFIX + digest

    def get_tokens(self) -> list[Token]:
        """Get the tokens"""
        redis = self.connection
        token_keys: list[str] = redis.keys(TOKENS_PREFIX + "*")  # type: ignore
        tokens = []
        for key in token_keys:
            token = self._token_from_hash(key)
            if token is not None:
                tokens.append(token)
        return tokens

    def _discover_token_key(self, input_token: Token) -> Optional[str]:
        """brute-force searching for tokens, for robust deletion"""
        redis = self.connection
        token_keys: list[str] = redis.keys(TOKENS_PREFIX + "*")  # type: ignore
        for key in token_keys:
            token = self._token_from_hash(key)
            if token == input_token:
                return key
        return None

    def delete_token(self, input_token: Token) -> None:
        """Delete the token"""
        redis = self.connection
        key = self._discover_token_key(input_token)
        if key is None:
            raise TokenNotFound
        redis.delete(key)

    def get_recovery_key(self) -> Optional[RecoveryKey]:
        """Get the recovery key"""
        redis = self.connection
        if redis.exists(RECOVERY_KEY_REDIS_KEY):
            return self._recovery_key_from_hash(RECOVERY_KEY_REDIS_KEY)
        return None

    def _store_recovery_key(self, recovery_key: RecoveryKey) -> None:
        self._store_model_as_hash(RECOVERY_KEY_REDIS_KEY, recovery_key)

    def _delete_recovery_key(self) -> None:
        """Delete the recovery key"""
        redis = self.connection
        redis.delete(RECOVERY_KEY_REDIS_KEY)

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
    def _is_date_key(key: str) -> bool:
        return key in [
            "created_at",
            "expires_at",
        ]

    @staticmethod
    def _prepare_model_dict(model_dict: dict[str, Any]) -> None:
        date_keys = [
            key for key in model_dict.keys() if RedisTokensRepository._is_date_key(key)
        ]
        for date in date_keys:
            if model_dict[date] != "None":
                model_dict[date] = datetime.fromisoformat(model_dict[date])
        for key in model_dict.keys():
            if model_dict[key] == "None":
                model_dict[key] = None

    def _model_dict_from_hash(self, redis_key: str) -> Optional[dict[str, Any]]:
        redis = self.connection
        if redis.exists(redis_key):
            token_dict: dict[str, Any] = redis.hgetall(redis_key)  # type: ignore
            RedisTokensRepository._prepare_model_dict(token_dict)
            return token_dict
        return None

    def _hash_as_model(self, redis_key: str, model_class):
        token_dict = self._model_dict_from_hash(redis_key)
        if token_dict is not None:
            return model_class(**token_dict)
        return None

    def _token_from_hash(self, redis_key: str) -> Optional[Token]:
        token = self._hash_as_model(redis_key, Token)
        if token is not None:
            token.created_at = token.created_at.replace(tzinfo=None)
            return token
        return None

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
