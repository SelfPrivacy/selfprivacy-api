import pytest

from selfprivacy_api.utils import hash_password
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


def test_hash_password_passes_password_over_stdin(mocker):
    process = mocker.Mock()
    process.communicate.return_value = [b"$6$hashed-password\n"]
    popen = mocker.patch("selfprivacy_api.utils.subprocess.Popen", return_value=process)

    assert hash_password("password with spaces") == "$6$hashed-password"
    popen.assert_called_once_with(
        ["mkpasswd", "-m", "sha-512", "--stdin"],
        shell=False,
        stdin=mocker.ANY,
        stdout=mocker.ANY,
        stderr=mocker.ANY,
    )
    process.communicate.assert_called_once_with(input=b"password with spaces")
