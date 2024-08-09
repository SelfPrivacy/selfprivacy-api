import pytest
from selfprivacy_api.utils.waitloop import wait_until_success


class Counter:
    def __init__(self):
        self.count = 0

    def tick(self):
        self.count += 1

    def reset(self):
        self.count = 0


def failing_operation(c: Counter) -> str:
    if c.count < 10:
        c.tick()
        raise ValueError("nooooope")
    return "yeees"


def test_wait_until_success():
    counter = Counter()

    with pytest.raises(TimeoutError):
        wait_until_success(
            lambda: failing_operation(counter), interval=0.1, timeout_sec=0.5
        )

    counter.reset()

    wait_until_success(
        lambda: failing_operation(counter), interval=0.1, timeout_sec=1.1
    )
