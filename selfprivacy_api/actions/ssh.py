"""Actions to manage the SSH."""

import gettext
from typing import Optional

from pydantic import BaseModel

from selfprivacy_api.utils import WriteUserData, ReadUserData, validate_ssh_public_key
from selfprivacy_api.utils import ensure_ssh_and_users_fields_exist
from selfprivacy_api.utils.localization import TranslateSystemMessage as t

from selfprivacy_api.repositories.users.exceptions import UserNotFound

_ = gettext.gettext


class UserdataSshSettings(BaseModel):
    """Settings for the SSH."""

    enable: bool = True
    passwordAuthentication: bool = False
    rootKeys: list[str] = []


class KeyNotFound(Exception):
    """Key not found"""

    @staticmethod
    def get_error_message(locale: str) -> str:
        return t.translate(text=_("Key not found"), locale=locale)


class KeyAlreadyExists(Exception):
    """Key already exists"""

    @staticmethod
    def get_error_message(locale: str) -> str:
        return t.translate(text=_("Key already exists"), locale=locale)


class InvalidPublicKey(Exception):
    """Invalid public key"""

    @staticmethod
    def get_error_message(locale: str) -> str:
        return t.translate(
            text=_(
                "Invalid key type. Only ssh-ed25519, ssh-rsa and ecdsa are supported"
            ),
            locale=locale,
        )


def enable_ssh():
    with WriteUserData() as data:
        if "ssh" not in data:
            data["ssh"] = {}
        data["ssh"]["enable"] = True


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
    enable: Optional[bool] = None,
) -> None:
    with WriteUserData() as data:
        if "ssh" not in data:
            data["ssh"] = {}
        if enable is not None:
            data["ssh"]["enable"] = enable


def create_ssh_key(username: str, ssh_key: str):
    """Create a new ssh key"""

    if not validate_ssh_public_key(ssh_key):
        raise InvalidPublicKey()

    with WriteUserData() as data:
        ensure_ssh_and_users_fields_exist(data)

        if username == data.get("username", None):
            if ssh_key in data.get("sshKeys", []):
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
                if "sshKeys" not in user:
                    user["sshKeys"] = []
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

    raise UserNotFound()
