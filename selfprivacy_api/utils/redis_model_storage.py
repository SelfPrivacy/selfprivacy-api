from datetime import datetime
from typing import Optional


def store_model_as_hash(redis, redis_key, model):
    for key, value in model.dict().items():
        if isinstance(value, datetime):
            value = value.isoformat()
        redis.hset(redis_key, key, str(value))


def hash_as_model(redis, redis_key: str, model_class):
    token_dict = _model_dict_from_hash(redis, redis_key)
    if token_dict is not None:
        return model_class(**token_dict)
    return None


def _prepare_model_dict(d: dict):
    for key in d.keys():
        if d[key] == "None":
            d[key] = None


def _model_dict_from_hash(redis, redis_key: str) -> Optional[dict]:
    if redis.exists(redis_key):
        token_dict = redis.hgetall(redis_key)
        _prepare_model_dict(token_dict)
        return token_dict
    return None
