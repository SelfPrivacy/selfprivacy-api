import pytest
import subprocess
from typing import List
from time import sleep

import pickle

import os
import sys

from os import path
from os.path import join, exists
from os import chdir

import selfprivacy_api
import tests

from selfprivacy_api.root_daemon.daemon import (
    get_available_commands,
    init,
    service_commands,
)
import selfprivacy_api.root_daemon.daemon as root_daemon
from selfprivacy_api.root_daemon.daemon import generate_file_body
from selfprivacy_api.root_daemon.root_interface import call_root_function
from selfprivacy_api.services import get_services


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
    services = get_services()
    assert len(commands) >= len(services) * len(service_commands) + len(services)
    for service in services:
        for unit in service.get_units():
            assert is_in_strings(commands, unit)
        for folder in service.get_folders():
            assert is_in_strings(commands, folder)


def test_module_paths():
    assert pickle.__file__ == get_python_module_path("pickle")


def get_python_module_path(module: str):
    # needs to be a standard module
    return (
        subprocess.check_output(
            ["python", "-c", f"import {module}; print({module}.__file__)"]
        )
        .decode("utf-8")
        .strip()
    )


def get_modules():
    return subprocess.check_output(["python", "-c", "help('modules')"])


# We then test the daemon which includes the fix
def test_pydantic_standalone_nofix():
    # check that we have it in test environment
    import pydantic

    # but we do NOT have it in test python
    with pytest.raises(Exception):
        subprocess.check_output(["python", "-c", "import pydantic"])


def test_generating_file_content():
    commands = get_available_commands()
    assert commands != []
    config_body = generate_file_body(commands)
    config_lines = config_body.splitlines()
    for command in commands:
        tokens = command.split(" ")
        cmd = tokens.pop(0)
        args = " ".join(tokens).strip()
        seen = False
        for line in config_lines:
            # if cmd in line and "args " + args in line:
            if cmd in line:
                seen = True
        if not seen:
            raise ValueError(
                "not all requested commands are present, could not find",
                cmd,
                "in",
                config_lines,
            )
    assert len(config_lines) == len(commands)


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


def make_pythonpath() -> str:
    return ":".join(sys.path)


def start_root_demon():

    old_dir = path.abspath(path.curdir)
    chdir(get_root_sp_directory())

    assert path.abspath(path.curdir) == get_root_sp_directory()

    # for some reason we do not have pythonpath set and so the process
    # cannot inherit it
    assert "PYTHONPATH" not in os.environ.keys()

    new_env = os.environ.copy()
    new_env["PYTHONPATH"] = make_pythonpath()
    assert "PYTHONPATH" in new_env.keys()

    # this is a prototype of how we need to run it`
    proc = subprocess.Popen(
        args=["python", "-m", "selfprivacy_api.root_daemon.daemon"],
        shell=False,
        env=new_env,
    )

    # check that it did not error out
    sleep(3)
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


def test_chowns():
    service = get_services()[0]
    command = ["chown", "selfprivacy", service.get_folders()[0]]

    proc = start_root_demon()
    answer = call_root_function(command)
    assert answer == " ".join(command)
    # confirm the loop still works
    answer = call_root_function(["blabla"])
    assert answer == "not permitted"

    proc.kill()


def test_send_valid_command():
    service = get_services()[0]
    proc = start_root_demon()

    command = ["systemctl", "start", service.get_units()[0]]
    answer = call_root_function(command)
    assert answer == " ".join(command)
    # confirm the loop still works
    answer = call_root_function(["blabla"])
    assert answer == "not permitted"

    proc.kill()
