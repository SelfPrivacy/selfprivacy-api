import asyncio
import pytest
import pytest_asyncio
from asyncio import streams
import redis
from typing import List

from selfprivacy_api.utils.redis_pool import RedisPool

from selfprivacy_api.jobs import Jobs, job_notifications

TEST_KEY = "test:test"
STOPWORD = "STOP"


@pytest.fixture()
def empty_redis(event_loop):
    r = RedisPool().get_connection()
    r.flushdb()
    assert r.config_get("notify-keyspace-events")["notify-keyspace-events"] == "AKE"
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


async def channel_reader(channel: redis.client.PubSub) -> List[dict]:
    result: List[dict] = []
    while True:
        # Mypy cannot correctly detect that it is a coroutine
        # But it is
        message: dict = await channel.get_message(ignore_subscribe_messages=True, timeout=None)  # type: ignore
        if message is not None:
            result.append(message)
            if message["data"] == STOPWORD:
                break
    return result


async def channel_reader_onemessage(channel: redis.client.PubSub) -> dict:
    while True:
        # Mypy cannot correctly detect that it is a coroutine
        # But it is
        message: dict = await channel.get_message(ignore_subscribe_messages=True, timeout=None)  # type: ignore
        if message is not None:
            return message


@pytest.mark.asyncio
async def test_pubsub(empty_redis, event_loop):
    # Adapted from :
    # https://redis.readthedocs.io/en/stable/examples/asyncio_examples.html
    # Sanity checking because of previous event loop bugs
    assert event_loop == asyncio.get_event_loop()
    assert event_loop == asyncio.events.get_event_loop()
    assert event_loop == asyncio.events.get_running_loop()

    reader = streams.StreamReader(34)
    assert event_loop == reader._loop
    f = reader._loop.create_future()
    f.set_result(3)
    await f

    r = RedisPool().get_connection_async()
    async with r.pubsub() as pubsub:
        await pubsub.subscribe("channel:1")
        future = asyncio.create_task(channel_reader(pubsub))

        await r.publish("channel:1", "Hello")
        # message: dict = await pubsub.get_message(ignore_subscribe_messages=True, timeout=5.0) # type: ignore
        # raise ValueError(message)
        await r.publish("channel:1", "World")
        await r.publish("channel:1", STOPWORD)

        messages = await future

        assert len(messages) == 3

        message = messages[0]
        assert "data" in message.keys()
        assert message["data"] == "Hello"
        message = messages[1]
        assert "data" in message.keys()
        assert message["data"] == "World"
        message = messages[2]
        assert "data" in message.keys()
        assert message["data"] == STOPWORD

    await r.close()


@pytest.mark.asyncio
async def test_keyspace_notifications_simple(empty_redis, event_loop):
    r = RedisPool().get_connection_async()
    await r.set(TEST_KEY, "I am not empty")
    async with r.pubsub() as pubsub:
        await pubsub.subscribe("__keyspace@0__:" + TEST_KEY)

        future_message = asyncio.create_task(channel_reader_onemessage(pubsub))
        empty_redis.set(TEST_KEY, "I am set!")
        message = await future_message
        assert message is not None
        assert message["data"] is not None
        assert message == {
            "channel": f"__keyspace@0__:{TEST_KEY}",
            "data": "set",
            "pattern": None,
            "type": "message",
        }


@pytest.mark.asyncio
async def test_keyspace_notifications(empty_redis, event_loop):
    pubsub = await RedisPool().subscribe_to_keys(TEST_KEY)
    async with pubsub:
        future_message = asyncio.create_task(channel_reader_onemessage(pubsub))
        empty_redis.set(TEST_KEY, "I am set!")
        message = await future_message
        assert message is not None
        assert message["data"] is not None
        assert message == {
            "channel": f"__keyspace@0__:{TEST_KEY}",
            "data": "set",
            "pattern": f"__keyspace@0__:{TEST_KEY}",
            "type": "pmessage",
        }


@pytest.mark.asyncio
async def test_keyspace_notifications_patterns(empty_redis, event_loop):
    pattern = "test*"
    pubsub = await RedisPool().subscribe_to_keys(pattern)
    async with pubsub:
        future_message = asyncio.create_task(channel_reader_onemessage(pubsub))
        empty_redis.set(TEST_KEY, "I am set!")
        message = await future_message
        assert message is not None
        assert message["data"] is not None
        assert message == {
            "channel": f"__keyspace@0__:{TEST_KEY}",
            "data": "set",
            "pattern": f"__keyspace@0__:{pattern}",
            "type": "pmessage",
        }


@pytest.mark.asyncio
async def test_keyspace_notifications_jobs(empty_redis, event_loop):
    pattern = "jobs:*"
    pubsub = await RedisPool().subscribe_to_keys(pattern)
    async with pubsub:
        future_message = asyncio.create_task(channel_reader_onemessage(pubsub))
        Jobs.add("testjob1", "test.test", "Testing aaaalll day")
        message = await future_message
        assert message is not None
        assert message["data"] is not None
        assert message["data"] == "hset"


async def reader_of_jobs() -> List[dict]:
    """
    Reads 3 job updates and exits
    """
    result: List[dict] = []
    async for message in job_notifications():
        result.append(message)
        if len(result) >= 3:
            break
    return result


@pytest.mark.asyncio
async def test_jobs_generator(empty_redis, event_loop):
    # Will read exactly 3 job messages
    future_messages = asyncio.create_task(reader_of_jobs())
    await asyncio.sleep(1)

    Jobs.add("testjob1", "test.test", "Testing aaaalll day")
    Jobs.add("testjob2", "test.test", "Testing aaaalll day")
    Jobs.add("testjob3", "test.test", "Testing aaaalll day")
    Jobs.add("testjob4", "test.test", "Testing aaaalll day")

    assert len(Jobs.get_jobs()) == 4
    r = RedisPool().get_connection()
    assert len(r.keys("jobs:*")) == 4

    messages = await future_messages
    assert len(messages) == 3
    channels = [message["channel"] for message in messages]
    operations = [message["data"] for message in messages]
    assert set(operations) == set(["hset"])  # all of them are hsets

    # Asserting that all of jobs emitted exactly one message
    jobs = Jobs.get_jobs()
    names = ["testjob1", "testjob2", "testjob3"]
    ids = [str(job.uid) for job in jobs if job.name in names]
    for id in ids:
        assert id in " ".join(channels)
    # Asserting that they came in order
    assert "testjob4" not in " ".join(channels)
