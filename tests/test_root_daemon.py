import pytest

from selfprivacy_api.root_daemon import get_available_commands, init, main, service_commands, services
import selfprivacy_api.root_daemon
from os.path import join

from typing import List


@pytest.fixture()
def test_socket(mocker, tmpdir):
    socket_path = join(tmpdir, "test_socket.s")
    mocker.patch(
        "selfprivacy_api.root_daemon.SOCKET_PATH",
        new=socket_path,
    )

def is_in_strings(list: List[str], piece: str):
    return any([piece in x for x in list])
    

def test_available_commands():
    commands = get_available_commands() 
    assert commands != []
    assert len(commands) >= len(services) * len(service_commands)
    for service in services:
        assert is_in_strings(commands, service)

def test_init():
    init()

def test_main():
    # main()
    pass
    
