import pytest
import redis
from typing import List

import subprocess
from subprocess import Popen, check_output, TimeoutExpired
from os import environ, path, set_blocking
from io import BufferedReader
from huey.exceptions import HueyException

from selfprivacy_api.utils.huey import huey, immediate, HUEY_DATABASE_NUMBER
from selfprivacy_api.utils.redis_pool import RedisPool, REDIS_SOCKET


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


# TODO: may be useful in other places too, move to utils/ tests common if using it somewhere
def read_all_ready_output(stream: BufferedReader) -> str:
    set_blocking(stream.fileno(), False)
    output: List[bytes] = []
    while True:
        line = stream.readline()
        raise ValueError(line)
        if line == b"":
            break
        else:
            output.append(line)

    set_blocking(stream.fileno(), True)

    result = b"".join(output)
    return result.decode("utf-8", "replace")


@pytest.fixture()
def not_immediate():
    assert environ["TEST_MODE"] == "true"

    old_immediate = huey.immediate
    environ["HUEY_QUEUES_FOR_TESTS"] = "Yes"
    huey.immediate = False
    assert huey.immediate is False

    yield

    del environ["HUEY_QUEUES_FOR_TESTS"]
    huey.immediate = old_immediate
    assert huey.immediate == old_immediate


@pytest.fixture()
def huey_socket_consumer(not_immediate):
    """
    Same as above, but with socketed redis
    """

    flush_huey_redis_forcefully()
    command = ["huey_consumer.py", "selfprivacy_api.task_registry.huey"]

    # First assert that consumer does not fail by itself
    # Idk yet how to do it more elegantly
    try:
        check_output(command, timeout=2)
    except TimeoutExpired:
        pass

    # Then open it for real
    consumer_handle = Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    assert path.exists(REDIS_SOCKET)

    yield consumer_handle

    consumer_handle.kill()


def test_huey_over_redis_socket(huey_socket_consumer):
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

    result = sum(2, 5)
    try:
        assert result(blocking=True, timeout=100) == 7

    except HueyException as error:
        if "timed out" in str(error):
            output = read_all_ready_output(huey_socket_consumer.stdout)
            errorstream = read_all_ready_output(huey_socket_consumer.stderr)
            raise TimeoutError(
                f"Huey timed out: {str(error)}",
                f"Consumer output: {output}",
                f"Consumer errorstream: {errorstream}",
            )
        else:
            raise error


@pytest.mark.xfail(reason="cannot yet schedule with sockets for some reason")
def test_huey_schedule(huey_queues_socket):
    # We do not schedule tasks anywhere, but concerning that it fails.
    sum.schedule((2, 5), delay=10)

    try:
        assert len(huey.scheduled()) == 1
    except AssertionError:
        raise ValueError("have wrong amount of scheduled tasks", huey.scheduled())
