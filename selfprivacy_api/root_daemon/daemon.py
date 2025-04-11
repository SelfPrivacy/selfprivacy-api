import sys

from typing import List
from typing import Dict

import os
import os.path

import socket as socket_module

import subprocess
from typing import Optional

from selfprivacy_api.root_daemon import SOCKET_PATH
from selfprivacy_api.services import get_services


BUFFER_SIZE = 1024

services = [
    # Check that it is the same as the names in systemd services.
    "bitwarden",
    "forgejo",
    "jitsimeet",
    "mailserver",
    "nextcloud",
    "ocserv",
    "pleroma",
    "prometheus",
    "roundcube",
    "postgresql",
]

service_folders: Dict[str, List[str]] = {
    # Fill by hand from service data
    "bitwarden": [],
    "forgejo": [],
    "gitea": [],
    "jitsimeet": [],
    "mailserver": [],
    "nextcloud": [],
    "ocserv": [],
    "pleroma": [],
    "prometheus": [],
    "roundcube": [],
}

service_commands = [
    "systemctl start",
    "systemctl stop",
    "systemctl restart",
]

static_commands = ["nixos rebuild" "nixos-store --gc"]

CHOWN_COMMAND = "chown selfprivacy"
# other_commands = [ CHOWN_COMMAND
# ]


def sync_with_dynamic_services():
    """
    We need to look at the file, then fetch service names
    and preferably service folders

    """


# it does not actually need to be there, doas allows for different
# config files?
DOAS_SETTINGS_LOCATION = "/etc/doas.conf"


def make_doas_row(command: str) -> str:

    tokens = command.split(" ")
    cmd = tokens.pop(0)
    args = tokens

    return f"permit nopass selfprivacy as root cmd {cmd} args {" ".join(args)}."


def generate_file_body(commands: List[str]) -> str:
    buffer = ""
    for command in commands:
        buffer += make_doas_row(command) + "\n"
    return buffer


def make_doas_conf(commands: List) -> None:
    with open(DOAS_SETTINGS_LOCATION, "w") as file:
        file.write(generate_file_body(commands))


def get_available_commands() -> List[str]:
    """
    Generate all commands with combinatorics.
    """
    # mounting and unmounting is handled by
    # selfprivacy being in mount group
    # chowning still needs root
    commands = []
    for command in service_commands:
        for service in services:
            # Concatenation of hardcoded strings
            commands.append(command + " " + service + ".service")

    chowns = [CHOWN_COMMAND + " " + folder for folder in service_folders]
    commands.extend(chowns)

    # chmods are done by selfprivacy user after chowning
    # they are not needed here

    commands.extend(static_commands)

    return commands


def init(socket_path=SOCKET_PATH) -> socket_module.socket:
    if os.path.exists(socket_path):
        os.remove(socket_path)
    sock = socket_module.socket(socket_module.AF_UNIX, socket_module.SOCK_STREAM)
    sock.bind(socket_path)
    assert os.path.exists(socket_path)
    return sock


def _spawn_shell(command_string: str) -> str:
    # We use sh to refrain from parsing and simplify logic
    # Our commands are hardcoded so sh does not present
    # an extra attack surface here

    # TODO: continuous forwarding of command output
    return subprocess.check_output(["sh", "-c", command_string]).decode("utf-8")


# A copy of the one from utils module.
# It is possible to remove this duplication but unfortunately it is not
# trivial and extra complexity does not worth it at the moment.
def get_test_mode() -> Optional[str]:
    return os.environ.get("TEST_MODE")


def _process_request(request: str, allowed_commands: str) -> str:
    for command in allowed_commands:
        if request == command:
            # explicitly only calling a _hardcoded_ command
            # ever
            # test mode made like this does not mae it more dangerous too
            if get_test_mode():
                return _spawn_shell(f'echo "{command}"')
            else:
                return _spawn_shell(command)
    else:
        return "not permitted"


TIMEOUT = 6.0


def _root_loop(socket: socket_module.socket, allowed_commands):
    socket.listen(1)

    socket.settimeout(TIMEOUT)
    while True:
        try:
            conn, addr = socket.accept()
        except TimeoutError:
            continue
        # conn is a new socket
        # TODO: check that it can inherit timeout
        conn.settimeout(TIMEOUT)
        pipe = conn.makefile("rw")

        # We accept a single line per connection for simplicity and safety
        line = pipe.readline()
        request = line.strip()
        answer = _process_request(request, allowed_commands)
        try:
            conn.send(answer.encode("utf-8"))
        except TimeoutError:
            pass
        pipe.close()
        conn.close()


def main(socket_path=SOCKET_PATH):
    allowed_commands = get_available_commands()
    print("\n".join(allowed_commands))

    sock = init(socket_path)
    _root_loop(sock, allowed_commands)


if __name__ == "__main__":
    main()
