import asyncio
import time
from time import sleep
from typing import Callable, Awaitable, Any, Optional

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


async def wait_until_true_async(
    readiness_checker: Callable[[], Awaitable[bool]],
    *,
    interval: float = DEFAULT_INTERVAL_SEC,
    timeout_sec: float = MAX_TIMEOUT,
) -> None:
    """
    Repeatedly awaits `readiness_checker()` until it returns True or timeout elapses.
    Raises TimeoutError on timeout.
    """
    deadline = time.monotonic() + timeout_sec

    # quick first check
    if await readiness_checker():
        return

    while time.monotonic() < deadline:
        await asyncio.sleep(interval)
        if await readiness_checker():
            return

    raise TimeoutError()


async def _is_fail_async(cal: Callable[[], Awaitable[Any]]) -> Optional[Exception]:
    try:
        await cal()
    except Exception as e:  # noqa: BLE001 – we re-raise context in TimeoutError below
        return e
    return None


async def wait_until_success_async(
    operation: Callable[[], Awaitable[Any]],
    *,
    interval: float = DEFAULT_INTERVAL_SEC,
    timeout_sec: float = MAX_TIMEOUT,
) -> None:
    """
    Repeatedly awaits `operation()` until it completes without raising.
    Raises TimeoutError with the last error if timeout elapses.
    """
    deadline = time.monotonic() + timeout_sec

    err = await _is_fail_async(operation)
    if err is None:
        return

    last_err: Optional[Exception] = err
    while time.monotonic() < deadline:
        await asyncio.sleep(interval)
        err = await _is_fail_async(operation)
        if err is None:
            return
        last_err = err

    if last_err is not None:
        raise TimeoutError(
            f"timed out on {operation} with error: "
            f"{last_err.__class__.__name__}: {last_err}"
        )
    raise TimeoutError(f"timed out waiting for {operation} to stop failing")
