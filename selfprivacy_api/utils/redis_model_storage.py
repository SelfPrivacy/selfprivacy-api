import uuid

from datetime import datetime
from typing import Optional
from enum import Enum


def store_model_as_hash(redis, redis_key, model):
    model_dict = model.model_dump()
    for key, value in model_dict.items():
        if isinstance(value, uuid.UUID):
            value = str(value)
        if isinstance(value, datetime):
            value = value.isoformat()
        if isinstance(value, Enum):
            value = value.value
        value = str(value)
        model_dict[key] = value

    redis.hset(redis_key, mapping=model_dict)


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
