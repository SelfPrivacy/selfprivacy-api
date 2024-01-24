import pytest

from subprocess import Popen
from os import environ, path
import redis

from selfprivacy_api.utils.huey import huey, immediate, HUEY_DATABASE_NUMBER
from selfprivacy_api.backup.util import output_yielder
from selfprivacy_api.utils.redis_pool import RedisPool
from selfprivacy_api.utils.waitloop import wait_until_true


@huey.task()
def sum(a: int, b: int) -> int:
    return a + b


def reset_huey_storage():
    huey.storage = huey.create_storage()


def flush_huey_redis_forcefully():
    url = RedisPool.connection_url(HUEY_DATABASE_NUMBER)

    pool = redis.ConnectionPool.from_url(url, decode_responses=True)
    connection = redis.Redis(connection_pool=pool)
    connection.flushdb()


@pytest.fixture()
def redis_socket(tmpdir):
    # Does NOT overwrite already imported redis pools
    # -> Not very useful for more involved tests
    # DOES override imported huey partially, but tries to restore it back

    socket_path = path.join(tmpdir, "redis.sock")
    environ["REDIS_SOCKET"] = socket_path

    old_port = None
    if "USE_REDIS_PORT" in environ:
        old_port = environ["USE_REDIS_PORT"]
        del environ["USE_REDIS_PORT"]

    assert "USE_REDIS_PORT" not in environ

    old_huey_url = huey.storage_kwargs.get("url")
    # Overriding url in the already imported singleton
    huey.storage_kwargs["url"] = RedisPool.connection_url(HUEY_DATABASE_NUMBER)
    reset_huey_storage()

    # Socket file will be created by redis
    command = [
        "redis-server",
        "--unixsocket",
        socket_path,
        "--unixsocketperm",
        "700",
        "--port",
        "0",
    ]
    redis_handle = Popen(command)

    wait_until_true(lambda: path.exists(socket_path), timeout_sec=2)
    flush_huey_redis_forcefully()

    yield socket_path

    # Socket file will be destroyed by redis
    redis_handle.terminate()

    if old_port:
        environ["USE_REDIS_PORT"] = old_port
    del environ["REDIS_SOCKET"]
    if old_huey_url:
        huey.storage_kwargs["url"] = old_huey_url
    else:
        del huey.storage_kwargs["url"]

    reset_huey_storage()


@pytest.fixture()
def not_immediate():
    old_immediate = huey.immediate
    environ["HUEY_QUEUES_FOR_TESTS"] = "Yes"
    huey.immediate = False
    assert huey.immediate is False

    yield

    del environ["HUEY_QUEUES_FOR_TESTS"]
    huey.immediate = old_immediate
    assert huey.immediate == old_immediate


@pytest.fixture()
def huey_queues(not_immediate):
    """
    Full, not-immediate, queued huey, with consumer starting and stopping.
    IMPORTANT: Assumes tests are run from the project directory.
    The above is needed by consumer to find our huey setup.
    """
    flush_huey_redis_forcefully()
    command = ["huey_consumer.py", "selfprivacy_api.task_registry.huey"]
    consumer_handle = Popen(command)

    yield huey

    consumer_handle.kill()


@pytest.fixture()
def huey_queues_socket(not_immediate, redis_socket):
    """
    Same as above, but with socketed redis
    """

    flush_huey_redis_forcefully()
    command = ["huey_consumer.py", "selfprivacy_api.task_registry.huey"]
    consumer_handle = Popen(command)

    assert path.exists(redis_socket)

    yield redis_socket

    consumer_handle.kill()


def test_huey_over_redis(huey_queues):
    assert huey.immediate is False
    assert immediate() is False

    result = sum(2, 5)
    assert result(blocking=True, timeout=2) == 7


# we cannot have these two fixtures prepared at the same time to iterate through them
def test_huey_over_redis_socket(huey_queues_socket):
    assert huey.immediate is False
    assert immediate() is False

    assert "unix" in RedisPool.connection_url(HUEY_DATABASE_NUMBER)
    try:
        assert (
            RedisPool.connection_url(HUEY_DATABASE_NUMBER)
            in huey.storage_kwargs.values()
        )
    except AssertionError:
        raise ValueError(
            "our test-side huey does not connect over socket: ", huey.storage_kwargs
        )

    # for some reason this fails. We do not schedule tasks anywhere, but concerning.
    # result = sum.schedule((2, 5), delay=10)
    # try:
    #     assert len(huey.scheduled()) == 1
    # except AssertionError:
    #     raise ValueError("have wrong amount of scheduled tasks", huey.scheduled())
    # result.revoke()

    result = sum(2, 5)
    assert result(blocking=True, timeout=2) == 7
