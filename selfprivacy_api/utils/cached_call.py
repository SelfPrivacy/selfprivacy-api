import pickle
from functools import wraps
from typing import Any, Optional, Callable

from selfprivacy_api.utils.redis_pool import RedisPool

CACHE_PREFIX = "exec_cache:"


def get_redis_object(key: str) -> Optional[Any]:
    redis = RedisPool().get_connection()
    binary_obj = redis.get(key)
    if binary_obj is None:
        return None
    return pickle.loads(binary_obj)


def save_redis_object(key: str, obj: Any, expire: Optional[int] = 60) -> None:
    redis = RedisPool().get_connection()
    binary_obj = pickle.dumps(obj)
    if expire:
        redis.setex(key, expire, binary_obj)
    else:
        redis.set(key, binary_obj)


def redis_cached_call(ttl: Optional[int] = 60) -> Callable[..., Callable]:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            key = f"{CACHE_PREFIX}{func.__name__}:{args}:{kwargs}"
            cached_value = get_redis_object(key)
            if cached_value is not None:
                return cached_value

            result = func(*args, **kwargs)

            save_redis_object(key, result, ttl)

            return result

        return wrapper

    return decorator
