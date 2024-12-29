import pytest
import subprocess
from typing import List
from time import sleep

from os import path
from os.path import join, exists
from os import chdir

import selfprivacy_api
import tests

from selfprivacy_api.root_daemon.daemon import (
    get_available_commands,
    init,
    service_commands,
    services,
)
import selfprivacy_api.root_daemon.daemon as root_daemon
from selfprivacy_api.root_daemon.root_interface import call_root_function


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


def get_root_sp_directory() -> str:
    package_file = selfprivacy_api.__file__
    tests_file = tests.__file__
    sp_dir = path.commonpath([package_file, tests_file])

    # raise ValueError(sp_dir,package_file, tests_file)

    return sp_dir


def start_root_demon():

    old_dir = path.abspath(path.curdir)
    chdir(get_root_sp_directory())

    assert path.abspath(path.curdir) == get_root_sp_directory()

    # this is a prototype of how we need to run it`
    proc = subprocess.Popen(
        args=["python", "-m", "selfprivacy_api.root_daemon.daemon"], shell=False
    )

    # check that it did not error out
    sleep(0.3)
    finished = proc.poll()
    assert finished is None

    chdir(old_dir)

    return proc


def test_send_command():
    proc = start_root_demon()

    answer = call_root_function(["blabla"])
    assert answer == "not permitted"
    # confirm the loop
    answer = call_root_function(["blabla"])
    assert answer == "not permitted"

    proc.kill()


def test_send_valid_command():
    proc = start_root_demon()

    command = ["systemctl", "start", "forgejo.service"]
    answer = call_root_function(command)
    assert answer == " ".join(command)
    # confirm the loop still works
    answer = call_root_function(["blabla"])
    assert answer == "not permitted"

    proc.kill()
