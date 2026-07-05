"""
Token repository using Redis as backend.
"""

from datetime import datetime, timezone
from hashlib import md5
from typing import Any, Optional

from opentelemetry import trace

from selfprivacy_api.exceptions.tokens import TokenNotFound
from selfprivacy_api.models.tokens.new_device_key import NewDeviceKey
from selfprivacy_api.models.tokens.recovery_key import RecoveryKey
from selfprivacy_api.models.tokens.token import Token
from selfprivacy_api.repositories.tokens.abstract_tokens_repository import (
    AbstractTokensRepository,
)
from selfprivacy_api.utils.redis_pool import RedisPool

TOKENS_PREFIX = "token_repo:tokens:"
NEW_DEVICE_KEY_REDIS_KEY = "token_repo:new_device_key"
RECOVERY_KEY_REDIS_KEY = "token_repo:recovery_key"

tracer = trace.get_tracer(__name__)


class RedisTokensRepository(AbstractTokensRepository):
    """
    Token repository using Redis as a backend
    """

    @property
    def connection(self):
        return RedisPool().get_connection_async()

    @staticmethod
    def token_key_for_device(device_name: str):
        md5_hash = md5(usedforsecurity=False)
        md5_hash.update(bytes(device_name, "utf-8"))
        digest = md5_hash.hexdigest()
        return TOKENS_PREFIX + digest

    @tracer.start_as_current_span("get_tokens")
    async def get_tokens(self) -> list[Token]:
        """Get the tokens"""
        redis = self.connection
        tokens = []
        async for key in redis.scan_iter(TOKENS_PREFIX + "*"):
            token = await self._token_from_hash(key)
            if token is not None:
                tokens.append(token)
        return tokens

    async def _discover_token_key(self, input_token: Token) -> Optional[str]:
        """brute-force searching for tokens, for robust deletion"""
        redis = self.connection
        async for key in redis.scan_iter(TOKENS_PREFIX + "*"):
            token = await self._token_from_hash(key)
            if token == input_token:
                return key
        return None

    async def delete_token(self, input_token: Token) -> None:
        """Delete the token"""
        redis = self.connection
        key = await self._discover_token_key(input_token)
        if key is None:
            raise TokenNotFound
        await redis.delete(key)

    async def get_recovery_key(self) -> Optional[RecoveryKey]:
        """Get the recovery key"""
        redis = self.connection
        if await redis.exists(RECOVERY_KEY_REDIS_KEY):
            return await self._recovery_key_from_hash(RECOVERY_KEY_REDIS_KEY)
        return None

    async def _store_recovery_key(self, recovery_key: RecoveryKey) -> None:
        await self._store_model_as_hash(RECOVERY_KEY_REDIS_KEY, recovery_key)

    async def _delete_recovery_key(self) -> None:
        """Delete the recovery key"""
        redis = self.connection
        await redis.delete(RECOVERY_KEY_REDIS_KEY)

    async def _store_new_device_key(self, new_device_key: NewDeviceKey) -> None:
        """Store new device key directly"""
        await self._store_model_as_hash(NEW_DEVICE_KEY_REDIS_KEY, new_device_key)

    async def delete_new_device_key(self) -> None:
        """Delete the new device key"""
        redis = self.connection
        await redis.delete(NEW_DEVICE_KEY_REDIS_KEY)

    @staticmethod
    def _token_redis_key(token: Token) -> str:
        return RedisTokensRepository.token_key_for_device(token.device_name)

    async def _store_token(self, new_token: Token):
        """Store a token directly"""
        key = RedisTokensRepository._token_redis_key(new_token)
        await self._store_model_as_hash(key, new_token)

    async def _decrement_recovery_token(self):
        """Decrement recovery key use count by one"""
        if await self.is_recovery_key_valid():
            recovery_key = await self.get_recovery_key()
            if recovery_key is None:
                return
            uses_left = recovery_key.uses_left
            if uses_left is not None:
                redis = self.connection
                await redis.hset(RECOVERY_KEY_REDIS_KEY, "uses_left", uses_left - 1)

    async def _get_stored_new_device_key(self) -> Optional[NewDeviceKey]:
        """Retrieves new device key that is already stored."""
        return await self._new_device_key_from_hash(NEW_DEVICE_KEY_REDIS_KEY)

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

    async def _model_dict_from_hash(self, redis_key: str) -> Optional[dict[str, Any]]:
        redis = self.connection
        if await redis.exists(redis_key):
            token_dict: dict[str, Any] = await redis.hgetall(redis_key)  # type: ignore
            RedisTokensRepository._prepare_model_dict(token_dict)
            return token_dict
        return None

    async def _hash_as_model(self, redis_key: str, model_class):
        token_dict = await self._model_dict_from_hash(redis_key)
        if token_dict is not None:
            return model_class(**token_dict)
        return None

    async def _token_from_hash(self, redis_key: str) -> Optional[Token]:
        token = await self._hash_as_model(redis_key, Token)
        if token is not None:
            token.created_at = token.created_at.replace(tzinfo=None)
            return token
        return None

    async def _recovery_key_from_hash(self, redis_key: str) -> Optional[RecoveryKey]:
        return await self._hash_as_model(redis_key, RecoveryKey)

    async def _new_device_key_from_hash(self, redis_key: str) -> Optional[NewDeviceKey]:
        return await self._hash_as_model(redis_key, NewDeviceKey)

    async def _store_model_as_hash(self, redis_key, model):
        redis = self.connection
        for key, value in model.model_dump().items():
            if isinstance(value, datetime):
                if value.tzinfo is None:
                    value = value.replace(tzinfo=timezone.utc)
                value = value.isoformat()
            await redis.hset(redis_key, key, str(value))
