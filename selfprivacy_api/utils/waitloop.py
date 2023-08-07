from time import sleep
from typing import Callable
from typing import Optional


def wait_until_true(
    readiness_checker: Callable[[], bool],
    *,
    interval: float = 0.1,
    timeout_sec: Optional[float] = None
):
    elapsed = 0.0
    if timeout_sec is None:
        timeout_sec = 10e16

    while (not readiness_checker()) and elapsed < timeout_sec:
        sleep(interval)
        elapsed += interval
    if elapsed > timeout_sec:
        raise TimeoutError()
