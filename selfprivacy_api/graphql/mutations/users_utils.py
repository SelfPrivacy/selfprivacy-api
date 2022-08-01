import re
from selfprivacy_api.utils import (
    WriteUserData,
    ReadUserData,
    is_username_forbidden,
)
from selfprivacy_api.utils import hash_password


def ensure_ssh_and_users_fields_exist(data):
    if "ssh" not in data:
        data["ssh"] = []
        data["ssh"]["rootKeys"] = []

    elif data["ssh"].get("rootKeys") is None:
        data["ssh"]["rootKeys"] = []

    if "sshKeys" not in data:
        data["sshKeys"] = []

    if "users" not in data:
        data["users"] = []


def create_user(username: str, password: str) -> tuple[bool, str, int]:
    """Create a new user"""

    # Check if password is null or none
    if password == "":
        return False, "Password is null", 400

    # Check if username is forbidden
    if is_username_forbidden(username):
        return False, "Username is forbidden", 409

    # Check is username passes regex
    if not re.match(r"^[a-z_][a-z0-9_]+$", username):
        return False, "Username must be alphanumeric", 400

    # Check if username less than 32 characters
    if len(username) >= 32:
        return False, "Username must be less than 32 characters", 400

    with ReadUserData() as data:
        ensure_ssh_and_users_fields_exist(data)

        # Return 409 if user already exists
        if data["username"] == username:
            return False, "User already exists", 409

        for data_user in data["users"]:
            if data_user["username"] == username:
                return False, "User already exists", 409

    hashed_password = hash_password(password)

    with WriteUserData() as data:
        ensure_ssh_and_users_fields_exist(data)

        data["users"].append(
            {
                "username": username,
                "hashedPassword": hashed_password,
                "sshKeys": [],
            }
        )

    return True, "User was successfully created!", 201


def delete_user(username: str) -> tuple[bool, str, int]:
    with WriteUserData() as data:
        ensure_ssh_and_users_fields_exist(data)

        if username == data["username"] or username == "root":
            return False, "Cannot delete main or root user", 400

        # Return 404 if user does not exist
        for data_user in data["users"]:
            if data_user["username"] == username:
                data["users"].remove(data_user)
                break
        else:
            return False, "User does not exist", 404

    return True, "User was deleted", 200


def update_user(username: str, password: str) -> tuple[bool, str, int]:
    # Check if password is null or none
    if password == "":
        return False, "Password is null", 400

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
                return False, "User does not exist", 404

    return True, "User was successfully updated", 200
