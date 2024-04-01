import asyncio
import pytest

from selfprivacy_api.utils.redis_pool import RedisPool

TEST_KEY = "test:test"


@pytest.fixture()
def empty_redis():
    r = RedisPool().get_connection()
    r.flushdb()
    yield r
    r.flushdb()


async def write_to_test_key():
    r = RedisPool().get_connection_async()
    async with r.pipeline(transaction=True) as pipe:
        ok1, ok2 = await pipe.set(TEST_KEY, "value1").set(TEST_KEY, "value2").execute()
        assert ok1
        assert ok2
    assert await r.get(TEST_KEY) == "value2"
    await r.close()


def test_async_connection(empty_redis):
    r = RedisPool().get_connection()
    assert not r.exists(TEST_KEY)
    # It _will_ report an error if it arises
    asyncio.run(write_to_test_key())
    # Confirming that we can read result from sync connection too
    assert r.get(TEST_KEY) == "value2"
