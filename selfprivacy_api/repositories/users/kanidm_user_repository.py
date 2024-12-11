from typing import Any, Optional, Union
import subprocess
import requests
import re
import logging

from selfprivacy_api.repositories.users.exceptions import (
    NoPasswordResetLinkFoundInResponse,
    UserAlreadyExists,
    UserNotFound,
)
from selfprivacy_api.repositories.users.exceptions_kanidm import (
    KanidmDidNotReturnAdminPassword,
    KanidmQueryError,
    KanidmReturnEmptyResponse,
    KanidmReturnUnknownResponseType,
)
from selfprivacy_api.utils import get_domain, temporary_env_var
from selfprivacy_api.utils.redis_pool import RedisPool
from selfprivacy_api.models.user import UserDataUser, UserDataUserOrigin
from selfprivacy_api.repositories.users.abstract_user_repository import (
    AbstractUserRepository,
)


KANIDM_URL = "https://127.0.0.1:3013"

redis = RedisPool().get_connection()

logger = logging.getLogger(__name__)

ADMIN_KANIDM_GROUPS = ["sp.admin"]


class KanidmAdminToken:  # TODO CHECK IS TOKEN CORRECT?
    @staticmethod
    def get() -> str:
        kanidm_admin_token = str(redis.get("kanidm:token"))

        if kanidm_admin_token is None:
            kanidm_admin_password = (
                KanidmAdminToken._reset_and_save_idm_admin_password()
            )

            kanidm_admin_token = KanidmAdminToken._create_and_save_token(
                kanidm_admin_password=kanidm_admin_password
            )

        return kanidm_admin_token

    @staticmethod
    def _create_and_save_token(kanidm_admin_password: str) -> str:
        with temporary_env_var(key="KANIDM_PASSWORD", value=kanidm_admin_password):
            subprocess.run(["kanidm", "login", "-D", "idm_admin"])

            output = subprocess.check_output(
                [
                    "kanidm",
                    "service-account",
                    "api-token",
                    "generate",
                    "--rw",
                    "selfprivacy",
                    "token2",
                ],
                text=True,
            )

        kanidm_admin_token = output.splitlines()[-1]

        redis.set("kanidm:token", kanidm_admin_token)
        return kanidm_admin_token

    @staticmethod
    def _reset_and_save_idm_admin_password() -> str:
        output = subprocess.check_output(
            [
                "kanidmd",
                "recover-account",
                "-c",
                "/etc/kanidm/server.toml",
                "idm_admin",
                "-o",
                "json",
            ],
            text=True,
        )

        match = re.search(r'"password":"([^"]+)"', output)
        if match:
            new_kanidm_admin_password = match.group(
                1
            )  # we have many not json strings in output
        else:
            raise KanidmDidNotReturnAdminPassword

        return new_kanidm_admin_password

    @staticmethod
    def _delete_kanidm_token_from_db() -> None:
        redis.delete("kanidm:token")


class KanidmUserRepository(AbstractUserRepository):
    @staticmethod
    def _check_response_type_and_not_empty(data_type: str, response_data: Any) -> None:
        """
        Validates the type and that content of the response data is not empty.

        Args:
            data_type (str): Expected type of response data ('list' or 'dict').
            response_data (any): Response data to validate.

        Raises:
            KanidmReturnEmptyResponse: If the response data is empty.
            KanidmReturnUnknownResponseType: If the response data is not of the expected type.
        """

        logging.info(response_data)

        if data_type == "list":
            if not isinstance(response_data, list):
                raise KanidmReturnUnknownResponseType(response_data=response_data)
            if not response_data:
                raise KanidmReturnEmptyResponse

        elif data_type == "dict":
            if not isinstance(response_data, dict):
                raise KanidmReturnUnknownResponseType(response_data=response_data)
            if not response_data.get("data"):
                raise KanidmReturnEmptyResponse

    @staticmethod
    def _check_user_origin_by_memberof(
        memberof: list[str] = [],
    ) -> UserDataUserOrigin:
        if sorted(memberof) == sorted(ADMIN_KANIDM_GROUPS):
            return UserDataUserOrigin.PRIMARY
        else:
            return UserDataUserOrigin.NORMAL

    @staticmethod
    def _send_query(endpoint: str, method: str = "GET", data=None) -> Union[dict, list]:
        request_method = getattr(requests, method.lower(), None)
        full_endpoint = f"{KANIDM_URL}/v1/{endpoint}"

        try:
            response = request_method(
                full_endpoint,
                json=data,
                headers={
                    "Authorization": f"Bearer {KanidmAdminToken.get()}",
                    "Content-Type": "application/json",
                },
                timeout=0.8,  # TODO: change timeout
                verify=False,  # TODO: REMOVE THIS NOT HALAL!!!!!
            )  # type: ignore
        except Exception as error:
            raise KanidmQueryError(error_text=str(error))

        response_data = response.json()
        logger.info(str(response))

        if response.status_code != 200:
            if isinstance(response_data, dict):
                plugin_error = response_data.get("plugin", {})
                if plugin_error.get("attrunique") == "duplicate value detected":
                    raise UserAlreadyExists  # TODO only user ?
            if isinstance(response_data, str):
                if response_data == "nomatchingentries":
                    raise UserNotFound

            raise KanidmQueryError(error_text=response.text)

    @staticmethod
    def create_user(
        username: str,
        directmemberof: Optional[list[str]] = None,
        memberof: Optional[list[str]] = None,
        displayname: Optional[str] = None,
    ) -> None:
        """
        Creates a new user."password" is a legacy field,
        please use generate_password_reset_link() instead.

        If displayname is None, it will default to the username.
        If email is None, it will default to username@get_domain().
        """

        data = {
            "attrs": {
                "name": [username],
                "displayname": [displayname if displayname else username],
                "mail": [f"{username}@{get_domain()}"],
                "class": ["user"],  # TODO read more about it
            }
        }

        if directmemberof:
            data["attrs"]["directmemberof"] = directmemberof
        if memberof:
            data["attrs"]["memberof"] = memberof

        KanidmUserRepository._send_query(
            endpoint="person",
            method="POST",
            data=data,
        )

    @staticmethod
    def get_users(
        exclude_primary: bool = False,
        exclude_root: bool = False,  # never return root
    ) -> list[UserDataUser]:
        """
        Gets a list of users with options to exclude specific user groups.
        The root user will never return.
        """
        users_data = KanidmUserRepository._send_query(endpoint="person", method="GET")

        KanidmUserRepository._check_response_type_and_not_empty(
            data_type="list", response_data=users_data
        )

        users = []
        for user in users_data:
            user_attrs = user.get("attrs", {})

            user_type = KanidmUserRepository._check_user_origin_by_memberof(
                memberof=user_attrs.get("memberof", [])
            )
            if exclude_primary and user_type == UserDataUserOrigin.PRIMARY:
                continue

            filled_user = UserDataUser(
                username=user_attrs["name"][0],
                user_type=user_type,
                ssh_keys=[],  # actions layer will full in this field
                directmemberof=user_attrs.get("directmemberof", []),
                memberof=user_attrs.get("memberof", []),
                displayname=user_attrs.get("displayname", None)[0],
                email=user_attrs.get("mail", None)[0],
            )

            users.append(filled_user)
        return users

    @staticmethod
    def delete_user(username: str) -> None:
        """Deletes an existing user"""

        KanidmUserRepository._send_query(endpoint=f"person/{username}", method="DELETE")

    @staticmethod
    def update_user(
        username: str,
        directmemberof: Optional[list[str]] = None,
        memberof: Optional[list[str]] = None,
        displayname: Optional[str] = None,
    ) -> None:
        """
        Update user information.
        Do not update the password, please
        use generate_password_reset_link() instead.
        """

        data = {
            "attrs": {
                "displayname": [displayname if displayname else username],
                "mail": [f"{username}@{get_domain()}"],
                "class": ["user"],  # TODO read more about it
            }
        }

        if directmemberof:
            data["attrs"]["directmemberof"] = directmemberof
        if memberof:
            data["attrs"]["memberof"] = memberof

        KanidmUserRepository._send_query(
            endpoint=f"person/{username}",
            method="PATCH",
            data=data,
        )

    @staticmethod
    def get_user_by_username(username: str) -> UserDataUser:
        """Retrieves user data (UserDataUser) by username"""
        user_data = KanidmUserRepository._send_query(
            endpoint=f"person/{username}",
            method="GET",
        )

        KanidmUserRepository._check_response_type_and_not_empty(
            data_type="dict", response_data=user_data
        )

        attrs = user_data["attrs"]

        return UserDataUser(
            username=attrs["name"][0],
            user_type=KanidmUserRepository._check_user_origin_by_memberof(
                memberof=attrs.get("memberof", [])
            ),
            ssh_keys=[],  # Actions layer will fill this field
            directmemberof=attrs.get("directmemberof", []),
            memberof=attrs.get("memberof", []),
            displayname=attrs.get("displayname", [None])[0],
            email=attrs.get("mail", [None])[0],
        )

    @staticmethod
    def generate_password_reset_link(username: str) -> str:
        """
        Do not reset the password, just generate a link to reset the password.
        Not implemented in JsonUserRepository.
        """
        data = KanidmUserRepository._send_query(
            endpoint=f"person/{username}/_credential/_update_intent",
            method="GET",
        )

        KanidmUserRepository._check_response_type_and_not_empty(
            data_type="dict", response_data=data
        )

        token = data.get("token", None)

        if not token:
            raise KanidmReturnEmptyResponse

        if token:
            return f"https://id.{get_domain()}/ui/reset?token={token}"

        raise NoPasswordResetLinkFoundInResponse
