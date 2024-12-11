from typing import List
# from subprocess import check_output
from selfprivacy_api.root_daemon import SOCKET_PATH, socket_module
from tests.test_common import get_test_mode


def call_root_function(cmd: List[str]) -> str:
    if get_test_mode():
        return "done"
    else:
        return _call_root_daemon(cmd)
        
def  _call_root_daemon(cmd: List[str]) -> str:
    return _write_to_daemon_socket(cmd)


def _write_to_daemon_socket(cmd: List[str]) -> str:
    sock = socket_module.socket(socket_module.AF_UNIX, socket_module.SOCK_STREAM)
    sock.connect(SOCKET_PATH)
    sock.send(" ".join(cmd).encode("utf-8")+b"\n")
    pipe = sock.makefile("rw")
    line = pipe.readline()
    return line

