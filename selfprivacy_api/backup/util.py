import subprocess
from os.path import exists
from typing import Generator


def output_yielder(command) -> Generator[str, None, None]:
    """Note: If you break during iteration, it kills the process"""
    with subprocess.Popen(
        command,
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    ) as handle:
        if handle is None or handle.stdout is None:
            raise ValueError("could not run command: ", command)

        try:
            for line in iter(handle.stdout.readline, ""):
                if "NOTICE:" not in line:
                    yield line
        except GeneratorExit:
            handle.kill()


def sync(src_path: str, dest_path: str):
    """a wrapper around rclone sync"""

    if not exists(src_path):
        raise ValueError("source dir for rclone sync must exist")

    rclone_command = ["rclone", "sync", "-P", src_path, dest_path]
    for raw_message in output_yielder(rclone_command):
        if "ERROR" in raw_message:
            raise ValueError(raw_message)
