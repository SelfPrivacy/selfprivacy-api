from time import sleep
from typing import Callable, Any, Optional

MAX_TIMEOUT = 10e16
DEFAULT_INTERVAL_SEC = 0.1


def wait_until_true(
    readiness_checker: Callable[[], bool],
    *,
    interval: float = DEFAULT_INTERVAL_SEC,
    timeout_sec: float = MAX_TIMEOUT,
):
    elapsed = 0.0

    while (not readiness_checker()) and elapsed < timeout_sec:
        sleep(interval)
        elapsed += interval
    if elapsed > timeout_sec:
        raise TimeoutError()


def is_fail(cal: Callable[[], Any]) -> Optional[Exception]:
    try:
        cal()
    except Exception as e:
        # We want it to be a logical True
        assert e
        return e
    return None


def wait_until_success(
    operation: Callable[[], Any],
    *,
    interval: float = DEFAULT_INTERVAL_SEC,
    timeout_sec: float = MAX_TIMEOUT,
):

    elapsed = 0.0
    error = is_fail(operation)

    while error and elapsed < timeout_sec:
        sleep(interval)
        elapsed += interval
        error = is_fail(operation)

    if elapsed >= timeout_sec:
        if isinstance(error, Exception):
            raise TimeoutError(
                "timed out on",
                operation,
                " with error: " + error.__class__.__name__ + ":" + str(error),
            )
        else:
            raise TimeoutError(
                "timed out waiting for an operation to stop failing", operation
            )
