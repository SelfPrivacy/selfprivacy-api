"""Actions to manage the SSH."""

import gettext
from typing import Optional

from pydantic import BaseModel

from selfprivacy_api.exceptions.users import UserNotFound
from selfprivacy_api.exceptions.users.ssh import (
    InvalidPublicKey,
    KeyAlreadyExists,
    KeyNotFound,
)
from selfprivacy_api.utils import (
    ReadUserData,
    WriteUserData,
    ensure_ssh_and_users_fields_exist,
    validate_ssh_public_key,
)

_ = gettext.gettext


class UserdataSshSettings(BaseModel):
    """Settings for the SSH."""

    enable: bool = True
    passwordAuthentication: bool = False
    rootKeys: list[str] = []


def enable_ssh():
    with WriteUserData() as data:
        data.setdefault("ssh", {})["enable"] = True


def get_ssh_settings() -> UserdataSshSettings:
    with ReadUserData() as data:
        if "ssh" not in data:
            return UserdataSshSettings()
        data["ssh"].setdefault("enable", True)
        data["ssh"].setdefault("passwordAuthentication", False)
        data["ssh"].setdefault("rootKeys", [])
        return UserdataSshSettings(**data["ssh"])


def set_ssh_settings(
    enable: Optional[bool] = None,
) -> None:
    with WriteUserData() as data:
        data.setdefault("ssh", {})
        if enable is not None:
            data["ssh"]["enable"] = enable


def create_ssh_key(username: str, ssh_key: str):
    """Create a new ssh key"""

    if not validate_ssh_public_key(ssh_key):
        raise InvalidPublicKey()

    with WriteUserData() as data:
        ensure_ssh_and_users_fields_exist(data)

        if username == data.get("username", None):
            _add_key_to_main_user(data, ssh_key)
        elif username == "root":
            _add_key_to_root(data, ssh_key)
        else:
            _add_key_to_regular_user(data, username, ssh_key)


def _add_key_to_main_user(data: dict, ssh_key: str) -> None:
    """Add SSH key to the main user"""
    if ssh_key in data.get("sshKeys", []):
        raise KeyAlreadyExists()
    data["sshKeys"].append(ssh_key)


def _add_key_to_root(data: dict, ssh_key: str) -> None:
    """Add SSH key to root user"""
    if ssh_key in data["ssh"]["rootKeys"]:
        raise KeyAlreadyExists()
    data["ssh"]["rootKeys"].append(ssh_key)


def _add_key_to_regular_user(data: dict, username: str, ssh_key: str) -> None:
    """Add SSH key to a regular user"""
    for user in data["users"]:
        if user["username"] == username:
            user.setdefault("sshKeys", [])
            if ssh_key in user["sshKeys"]:
                raise KeyAlreadyExists()
            user["sshKeys"].append(ssh_key)
            return

    raise UserNotFound()


def remove_ssh_key(username: str, ssh_key: str):
    """Delete a ssh key"""

    with WriteUserData() as data:
        ensure_ssh_and_users_fields_exist(data)

        if username == "root":
            if ssh_key in data["ssh"]["rootKeys"]:
                data["ssh"]["rootKeys"].remove(ssh_key)
                return

            raise KeyNotFound()

        if username == data.get("username", None):
            if ssh_key in data.get("sshKeys", []):
                data["sshKeys"].remove(ssh_key)
                return

            raise KeyNotFound()

        for user in data["users"]:
            if user["username"] == username:
                user.setdefault("sshKeys", [])
                if ssh_key in user["sshKeys"]:
                    user["sshKeys"].remove(ssh_key)
                    return

                raise KeyNotFound()

    raise UserNotFound()


def get_ssh_keys(username: str) -> list:
    """Get all SSH keys for a user"""

    with ReadUserData() as data:
        ensure_ssh_and_users_fields_exist(data)

        if username == "root":
            return data["ssh"]["rootKeys"]

        if username == data.get("username", None):
            return data.get("sshKeys", [])

        for user in data["users"]:
            if user["username"] == username:
                if "sshKeys" in user:
                    return user["sshKeys"]
                return []

    raise UserNotFound(log=False)
