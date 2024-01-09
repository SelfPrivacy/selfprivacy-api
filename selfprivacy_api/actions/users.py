"""Actions to manage the users."""
import re
from typing import Optional
from pydantic import BaseModel
from enum import Enum
from selfprivacy_api.utils import (
    ReadUserData,
    WriteUserData,
    hash_password,
    is_username_forbidden,
)


class UserDataUserOrigin(Enum):
    """Origin of the user in the user data"""

    NORMAL = "NORMAL"
    PRIMARY = "PRIMARY"
    ROOT = "ROOT"


class UserDataUser(BaseModel):
    """The user model from the userdata file"""

    username: str
    ssh_keys: list[str]
    origin: UserDataUserOrigin


def ensure_ssh_and_users_fields_exist(data):
    if "ssh" not in data:
        data["ssh"] = {}
        data["ssh"]["rootKeys"] = []

    elif data["ssh"].get("rootKeys") is None:
        data["ssh"]["rootKeys"] = []

    if "sshKeys" not in data:
        data["sshKeys"] = []

    if "users" not in data:
        data["users"] = []


def get_users(
    exclude_primary: bool = False,
    exclude_root: bool = False,
) -> list[UserDataUser]:
    """Get the list of users"""
    users = []
    with ReadUserData() as user_data:
        ensure_ssh_and_users_fields_exist(user_data)
        users = [
            UserDataUser(
                username=user["username"],
                ssh_keys=user.get("sshKeys", []),
                origin=UserDataUserOrigin.NORMAL,
            )
            for user in user_data["users"]
        ]
        if not exclude_primary and "username" in user_data.keys():
            users.append(
                UserDataUser(
                    username=user_data["username"],
                    ssh_keys=user_data["sshKeys"],
                    origin=UserDataUserOrigin.PRIMARY,
                )
            )
        if not exclude_root:
            users.append(
                UserDataUser(
                    username="root",
                    ssh_keys=user_data["ssh"]["rootKeys"],
                    origin=UserDataUserOrigin.ROOT,
                )
            )
    return users


class UsernameForbidden(Exception):
    """Attemted to create a user with a forbidden username"""

    pass


class UserAlreadyExists(Exception):
    """Attemted to create a user that already exists"""

    pass


class UsernameNotAlphanumeric(Exception):
    """Attemted to create a user with a non-alphanumeric username"""

    pass


class UsernameTooLong(Exception):
    """Attemted to create a user with a too long username. Username must be less than 32 characters"""

    pass


class PasswordIsEmpty(Exception):
    """Attemted to create a user with an empty password"""

    pass


class InvalidConfiguration(Exception):
    """The userdata is broken"""

    pass


def create_user(username: str, password: str):
    if password == "":
        raise PasswordIsEmpty("Password is empty")

    if is_username_forbidden(username):
        raise UsernameForbidden("Username is forbidden")

    if not re.match(r"^[a-z_][a-z0-9_]+$", username):
        raise UsernameNotAlphanumeric(
            "Username must be alphanumeric and start with a letter"
        )

    if len(username) >= 32:
        raise UsernameTooLong("Username must be less than 32 characters")

    with ReadUserData() as user_data:
        ensure_ssh_and_users_fields_exist(user_data)
        if "username" not in user_data.keys():
            raise InvalidConfiguration(
                "Broken config: Admin name is not defined. Consider recovery or add it manually"
            )
        if username == user_data["username"]:
            raise UserAlreadyExists("User already exists")
        if username in [user["username"] for user in user_data["users"]]:
            raise UserAlreadyExists("User already exists")

    hashed_password = hash_password(password)

    with WriteUserData() as user_data:
        ensure_ssh_and_users_fields_exist(user_data)

        user_data["users"].append(
            {"username": username, "sshKeys": [], "hashedPassword": hashed_password}
        )


class UserNotFound(Exception):
    """Attemted to get a user that does not exist"""

    pass


class UserIsProtected(Exception):
    """Attemted to delete a user that is protected"""

    pass


def delete_user(username: str):
    with WriteUserData() as user_data:
        ensure_ssh_and_users_fields_exist(user_data)
        if username == user_data["username"] or username == "root":
            raise UserIsProtected("Cannot delete main or root user")

        for data_user in user_data["users"]:
            if data_user["username"] == username:
                user_data["users"].remove(data_user)
                break
        else:
            raise UserNotFound("User did not exist")


def update_user(username: str, password: str):
    if password == "":
        raise PasswordIsEmpty("Password is empty")

    hashed_password = hash_password(password)

    with WriteUserData() as data:
        ensure_ssh_and_users_fields_exist(data)

        if username == data["username"]:
            data["hashedMasterPassword"] = hashed_password

        # Return 404 if user does not exist
        else:
            for data_user in data["users"]:
                if data_user["username"] == username:
                    data_user["hashedPassword"] = hashed_password
                    break
            else:
                raise UserNotFound("User does not exist")


def get_user_by_username(username: str) -> Optional[UserDataUser]:
    with ReadUserData() as data:
        ensure_ssh_and_users_fields_exist(data)

        if username == "root":
            return UserDataUser(
                origin=UserDataUserOrigin.ROOT,
                username="root",
                ssh_keys=data["ssh"]["rootKeys"],
            )

        if username == data["username"]:
            return UserDataUser(
                origin=UserDataUserOrigin.PRIMARY,
                username=username,
                ssh_keys=data["sshKeys"],
            )

        for user in data["users"]:
            if user["username"] == username:
                if "sshKeys" not in user:
                    user["sshKeys"] = []

                return UserDataUser(
                    origin=UserDataUserOrigin.NORMAL,
                    username=username,
                    ssh_keys=user["sshKeys"],
                )

        return None
