import pytest
import os
import asyncio
import threading
import subprocess

from selfprivacy_api.root_daemon import (
    get_available_commands,
    init,
    main,
    service_commands,
    services,
)
import selfprivacy_api
import selfprivacy_api.root_daemon as root_daemon
from selfprivacy_api.utils.root_interface import call_root_function
from os.path import join, exists

from typing import List


@pytest.fixture()
def test_socket(mocker, tmpdir):
    socket_path = join(tmpdir, "test_socket.s")
    mocker.patch(
        "selfprivacy_api.root_daemon.SOCKET_PATH",
        new=socket_path,
    )
    return socket_path


def is_in_strings(list: List[str], piece: str):
    return any([piece in x for x in list])


def test_available_commands():
    commands = get_available_commands()
    assert commands != []
    assert len(commands) >= len(services) * len(service_commands)
    for service in services:
        assert is_in_strings(commands, service)


def test_init():
    sock = init()
    assert exists(root_daemon.SOCKET_PATH)
    assert sock is not None


def test_send_command():
    root_daemon_file = selfprivacy_api.root_daemon.__file__
    # this is a prototype of how we need to run it`
    proc = subprocess.Popen(args=["python", root_daemon_file], shell=False)

    # thread = threading.Thread(target=start_root_daemon,args=[])
    # thread.start()
    answer = call_root_function("blabla")
    assert answer == "done"

    proc.kill()
    # thread.join(timeout=1.0)
