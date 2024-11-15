from typing import Optional


from selfprivacy_api.models.user import UserDataUser, UserDataUserOrigin
from selfprivacy_api.utils import (
    ReadUserData,
    WriteUserData,
    ensure_ssh_and_users_fields_exist,
    hash_password,
)
from selfprivacy_api.repositories.users.abstract_user_repository import (
    AbstractUserRepository,
)
from selfprivacy_api.repositories.users.exceptions import (
    InvalidConfiguration,
    UserAlreadyExists,
    UserIsProtected,
    UserNotFound,
    PasswordIsEmpty,
)


class JsonUserRepository(AbstractUserRepository):
    @staticmethod
    def _check_and_hash_password(password: str):
        if password == "":
            raise PasswordIsEmpty("Password is empty")

        return hash_password(password)

    @staticmethod
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

    @staticmethod
    def create_user(username: str, password: str) -> None:
        hashed_password = JsonUserRepository._check_and_hash_password(password)

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

        with WriteUserData() as user_data:
            ensure_ssh_and_users_fields_exist(user_data)

            user_data["users"].append(
                {"username": username, "sshKeys": [], "hashedPassword": hashed_password}
            )

    @staticmethod
    def delete_user(username: str) -> None:
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

    @staticmethod
    def update_user(username: str, password: str) -> None:
        hashed_password = JsonUserRepository._check_and_hash_password(password)

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

    @staticmethod
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
