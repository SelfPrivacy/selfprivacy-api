import pytest

from subprocess import Popen
from os import environ


# from selfprivacy_api.backup.util import output_yielder
from selfprivacy_api.utils.huey import huey


@huey.task()
def sum(a: int, b: int) -> int:
    return a + b


@pytest.fixture()
def huey_queues():
    """
    Full, not-immediate, queued huey, with consumer starting and stopping.
    IMPORTANT: Assumes tests are run from the project directory.
    The above is needed by consumer to find our huey setup.
    """
    old_immediate = huey.immediate

    environ["HUEY_QUEUES_FOR_TESTS"] = "Yes"
    command = ["huey_consumer.py", "selfprivacy_api.task_registry.huey"]
    huey.immediate = False
    assert huey.immediate is False
    consumer_handle = Popen(command)

    yield huey

    consumer_handle.terminate()
    del environ["HUEY_QUEUES_FOR_TESTS"]
    huey.immediate = old_immediate
    assert huey.immediate == old_immediate


def test_huey(huey_queues):
    result = sum(2, 5)
    assert result(blocking=True) == 7
