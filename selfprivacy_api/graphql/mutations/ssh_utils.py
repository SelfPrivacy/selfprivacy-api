from selfprivacy_api.graphql.common_types.user import ensure_ssh_and_users_fields_exist
from selfprivacy_api.utils import (
    WriteUserData,
    validate_ssh_public_key,
)


def create_ssh_key(username: str, ssh_key: str) -> tuple[bool, str, int]:
    """Create a new ssh key"""

    if not validate_ssh_public_key(ssh_key):
        return (
            False,
            "Invalid key type. Only ssh-ed25519 and ssh-rsa are supported",
            400,
        )

    with WriteUserData() as data:
        ensure_ssh_and_users_fields_exist(data)

        if username == data["username"]:
            if ssh_key in data["sshKeys"]:
                return False, "Key already exists", 409

            data["sshKeys"].append(ssh_key)
            return True, "New SSH key successfully written", 201

        if username == "root":
            if ssh_key in data["ssh"]["rootKeys"]:
                return False, "Key already exists", 409

            data["ssh"]["rootKeys"].append(ssh_key)
            return True, "New SSH key successfully written", 201

        for user in data["users"]:
            if user["username"] == username:
                if ssh_key in user["sshKeys"]:
                    return False, "Key already exists", 409

                user["sshKeys"].append(ssh_key)
                return True, "New SSH key successfully written", 201

        return False, "User not found", 404


def remove_ssh_key(username: str, ssh_key: str) -> tuple[bool, str, int]:
    """Delete a ssh key"""

    with WriteUserData() as data:
        ensure_ssh_and_users_fields_exist(data)

        if username == "root":
            if ssh_key in data["ssh"]["rootKeys"]:
                data["ssh"]["rootKeys"].remove(ssh_key)
                return True, "SSH key deleted", 200

            return False, "Key not found", 404

        if username == data["username"]:
            if ssh_key in data["sshKeys"]:
                data["sshKeys"].remove(ssh_key)
                return True, "SSH key deleted", 200

            return False, "Key not found", 404

        for user in data["users"]:
            if user["username"] == username:
                if ssh_key in user["sshKeys"]:
                    user["sshKeys"].remove(ssh_key)
                    return True, "SSH key deleted", 200

                return False, "Key not found", 404

    return False, "User not found", 404
