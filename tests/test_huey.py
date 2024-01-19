import pytest

from subprocess import Popen
from os import environ, path

from selfprivacy_api.utils.huey import huey, immediate


@huey.task()
def sum(a: int, b: int) -> int:
    return a + b


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
    command = ["huey_consumer.py", "selfprivacy_api.task_registry.huey"]
    consumer_handle = Popen(command)

    yield huey

    consumer_handle.terminate()


def test_huey(huey_queues):
    assert huey.immediate is False
    assert immediate() is False

    result = sum(2, 5)
    assert result(blocking=True) == 7
