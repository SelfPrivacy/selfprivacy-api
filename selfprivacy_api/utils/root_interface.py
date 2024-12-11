from typing import List
from time import sleep

# from subprocess import check_output
from selfprivacy_api.root_daemon import SOCKET_PATH, socket_module
from tests.test_common import get_test_mode


def call_root_function(cmd: List[str]) -> str:
    assert isinstance(cmd, List)
    return _call_root_daemon(cmd)


def _call_root_daemon(cmd: List[str]) -> str:
    return _write_to_daemon_socket(cmd)


def _write_to_daemon_socket(cmd: List[str]) -> str:
    sock = socket_module.socket(socket_module.AF_UNIX, socket_module.SOCK_STREAM)
    sock.connect(SOCKET_PATH)
    payload = " ".join(cmd).encode("utf-8") + b"\n"
    sock.send(payload)
    pipe = sock.makefile("r")
    answer = pipe.readline()
    pipe.close()
    sock.close()
    return answer
