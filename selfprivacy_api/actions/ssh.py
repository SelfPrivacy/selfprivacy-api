"""Actions to manage the SSH."""

from typing import Optional
from pydantic import BaseModel

from selfprivacy_api.utils import WriteUserData, ReadUserData, validate_ssh_public_key
from selfprivacy_api.repositories.users.exceptions import UserNotFound
from selfprivacy_api.utils import ensure_ssh_and_users_fields_exist


def enable_ssh():
    with WriteUserData() as data:
        if "ssh" not in data:
            data["ssh"] = {}
        data["ssh"]["enable"] = True


class UserdataSshSettings(BaseModel):
    """Settings for the SSH."""

    enable: bool = True
    passwordAuthentication: bool = True
    rootKeys: list[str] = []


def get_ssh_settings() -> UserdataSshSettings:
    with ReadUserData() as data:
        if "ssh" not in data:
            return UserdataSshSettings()
        if "enable" not in data["ssh"]:
            data["ssh"]["enable"] = True
        if "passwordAuthentication" not in data["ssh"]:
            data["ssh"]["passwordAuthentication"] = False
        if "rootKeys" not in data["ssh"]:
            data["ssh"]["rootKeys"] = []
        return UserdataSshSettings(**data["ssh"])


def set_ssh_settings(
    enable: Optional[bool] = None, password_authentication: Optional[bool] = None
) -> None:
    with WriteUserData() as data:
        if "ssh" not in data:
            data["ssh"] = {}
        if enable is not None:
            data["ssh"]["enable"] = enable
        if password_authentication is not None:
            data["ssh"]["passwordAuthentication"] = password_authentication


class KeyAlreadyExists(Exception):
    """Key already exists"""

    pass


class InvalidPublicKey(Exception):
    """Invalid public key"""

    pass


def create_ssh_key(username: str, ssh_key: str):
    """Create a new ssh key"""

    if not validate_ssh_public_key(ssh_key):
        raise InvalidPublicKey()

    with WriteUserData() as data:
        ensure_ssh_and_users_fields_exist(data)

        if username == data["username"]:
            if ssh_key in data["sshKeys"]:
                raise KeyAlreadyExists()

            data["sshKeys"].append(ssh_key)
            return

        if username == "root":
            if ssh_key in data["ssh"]["rootKeys"]:
                raise KeyAlreadyExists()

            data["ssh"]["rootKeys"].append(ssh_key)
            return

        for user in data["users"]:
            if user["username"] == username:
                if "sshKeys" not in user:
                    user["sshKeys"] = []
                if ssh_key in user["sshKeys"]:
                    raise KeyAlreadyExists()

                user["sshKeys"].append(ssh_key)
                return

        raise UserNotFound()


class KeyNotFound(Exception):
    """Key not found"""

    pass


def remove_ssh_key(username: str, ssh_key: str):
    """Delete a ssh key"""

    with WriteUserData() as data:
        ensure_ssh_and_users_fields_exist(data)

        if username == "root":
            if ssh_key in data["ssh"]["rootKeys"]:
                data["ssh"]["rootKeys"].remove(ssh_key)
                return

            raise KeyNotFound()

        if username == data["username"]:
            if ssh_key in data["sshKeys"]:
                data["sshKeys"].remove(ssh_key)
                return

            raise KeyNotFound()

        for user in data["users"]:
            if user["username"] == username:
                if "sshKeys" not in user:
                    user["sshKeys"] = []
                if ssh_key in user["sshKeys"]:
                    user["sshKeys"].remove(ssh_key)
                    return

                raise KeyNotFound()

    raise UserNotFound()
