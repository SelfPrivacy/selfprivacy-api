import asyncio
import pickle
from functools import wraps
from typing import Any, Optional, Callable

from selfprivacy_api.utils.redis_pool import RedisPool

CACHE_PREFIX = "exec_cache:"


async def get_redis_object(key: str) -> Optional[Any]:
    redis = RedisPool().get_connection_async()
    binary_obj = await redis.get(key)
    if binary_obj is None:
        return None
    return pickle.loads(binary_obj)


async def save_redis_object(key: str, obj: Any, expire: Optional[int] = 60) -> None:
    redis = RedisPool().get_connection_async()
    binary_obj = pickle.dumps(obj)
    if expire:
        await redis.setex(key, expire, binary_obj)
    else:
        await redis.set(key, binary_obj)


def redis_cached_call(ttl: Optional[int] = 60) -> Callable[..., Callable]:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            key = f"{CACHE_PREFIX}{func.__name__}:{args}:{kwargs}"
            cached_value = await get_redis_object(key)
            if cached_value is not None:
                return cached_value

            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            await save_redis_object(key, result, ttl)

            return result

        return wrapper

    return decorator
