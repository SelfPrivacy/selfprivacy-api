import subprocess

from selfprivacy_api.exceptions.users import PasswordHasInvalidChars


def hash_password(password: str) -> str:
    if any(character in password for character in "\r\n\0"):
        raise PasswordHasInvalidChars()

    hashing_command = ["mkpasswd", "-m", "sha-512", "--stdin"]
    password_hash_process_descriptor = subprocess.Popen(
        hashing_command,
        shell=False,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    hashed_password = password_hash_process_descriptor.communicate(
        input=password.encode("utf-8")
    )[0]
    return hashed_password.decode("ascii").rstrip()
