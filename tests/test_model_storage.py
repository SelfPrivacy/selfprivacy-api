import pytest

from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from selfprivacy_api.utils.redis_model_storage import store_model_as_hash, hash_as_model
from selfprivacy_api.utils.redis_pool import RedisPool

TEST_KEY = "model_storage"
redis = RedisPool().get_connection()


@pytest.fixture()
def clean_redis():
    redis.delete(TEST_KEY)


class DummyModel(BaseModel):
    name: str
    date: Optional[datetime]


def test_store_retrieve():
    model = DummyModel(name="test", date=datetime.now())
    store_model_as_hash(redis, TEST_KEY, model)
    assert hash_as_model(redis, TEST_KEY, DummyModel) == model


def test_store_retrieve_none():
    model = DummyModel(name="test", date=None)
    store_model_as_hash(redis, TEST_KEY, model)
    assert hash_as_model(redis, TEST_KEY, DummyModel) == model
