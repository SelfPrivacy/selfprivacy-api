from json import JSONDecodeError
from typing import Any, Optional, Union
import subprocess
import re
import logging
import requests  # type: ignore

from selfprivacy_api.models.group import Group
from selfprivacy_api.repositories.users.exceptions import (
    NoPasswordResetLinkFoundInResponse,
    UserAlreadyExists,
    UserNotFound,
    UserOrGroupNotFound,
)
from selfprivacy_api.repositories.users.exceptions_kanidm import (
    FailedToGetValidKanidmToken,
    KanidmCliSubprocessError,
    KanidmDidNotReturnAdminPassword,
    KanidmQueryError,
    KanidmReturnEmptyResponse,
    KanidmReturnUnknownResponseType,
)
from selfprivacy_api.services import KANIDM_A_RECORD
from selfprivacy_api.utils import get_domain, temporary_env_var
from selfprivacy_api.utils.redis_pool import RedisPool
from selfprivacy_api.models.user import UserDataUser, UserDataUserOrigin
from selfprivacy_api.repositories.users.abstract_user_repository import (
    AbstractUserRepository,
)

DOMAIN = get_domain()

REDIS_TOKEN_KEY = "kanidm:token"
redis = RedisPool().get_connection()

KANIDM_URL = "https://127.0.0.1:3013"
ADMIN_GROUPS = ["sp.admins"]
DEFAULT_GROUPS = [f"idm_all_persons@{DOMAIN}", f"idm_all_accounts@{DOMAIN}"]

logger = logging.getLogger(__name__)


class KanidmAdminToken:
    """
    Manages the administrative token for Kanidm.

    Methods:
        get() -> str:
            Retrieves the current administrative token. If absent, resets the admin password and creates a new token.

        _create_and_save_token(kanidm_admin_password: str) -> str:
            Creates a new token using the admin password and saves it to Redis.

        _reset_and_save_idm_admin_password() -> str:
            Resets the Kanidm admin password and returns the new password.

        _delete_kanidm_token_from_db() -> None:
            Deletes the admin token from Redis.

        _is_token_valid() -> bool:
            Sends a request to kanidm to check the validity of the token.
    """

    @staticmethod
    def get() -> str:
        kanidm_admin_token = redis.get(REDIS_TOKEN_KEY)

        if kanidm_admin_token:
            if KanidmAdminToken._is_token_valid(kanidm_admin_token):  # type: ignore
                return kanidm_admin_token  # type: ignore

        logging.warning("Kanidm admin token is missing or invalid. Regenerating.")

        kanidm_admin_password = KanidmAdminToken._reset_and_save_idm_admin_password()
        kanidm_admin_token = KanidmAdminToken._create_and_save_token(
            kanidm_admin_password=kanidm_admin_password
        )

        return kanidm_admin_token

    @staticmethod
    def _create_and_save_token(kanidm_admin_password: str) -> str:
        with temporary_env_var(key="KANIDM_PASSWORD", value=kanidm_admin_password):
            try:
                subprocess.run(["kanidm", "login", "-D", "idm_admin"], check=True)

                output = subprocess.check_output(
                    [
                        "kanidm",
                        "service-account",
                        "api-token",
                        "generate",
                        "--rw",
                        "sp.selfprivacy-api.service-account",
                        "kanidm_service_account_token",
                    ],
                    text=True,
                )
            except subprocess.CalledProcessError as error:
                logger.error(f"Error creating Kanidm token: {str(error.output)}")
                raise KanidmCliSubprocessError(error=str(error.output))

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
            )  # we have many non-JSON strings in output
        else:
            raise KanidmDidNotReturnAdminPassword

        return new_kanidm_admin_password

    @staticmethod
    def _is_token_valid(token: str) -> bool:
        endpoint = f"{KANIDM_URL}/v1/person/root"
        try:
            response = requests.get(
                endpoint,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                timeout=1,
                verify=False,  # TODO: REMOVE THIS NOT HALAL!!!!!
            )

        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.HTTPError,
        ) as error:
            raise KanidmQueryError(
                error_text=f"Kanidm is not responding to requests. Error: {str(error)}",
                endpoint=endpoint,
                method="GET",
            )

        except Exception as error:
            raise KanidmQueryError(error_text=error, endpoint=endpoint)

        response_data = response.json()

        # we do not handle the other errors, this is handled by the main function in KanidmUserRepository._send_query
        if response.status_code != 200:
            if isinstance(response_data, str) and response_data == "notauthenticated":
                logger.error("Kanidm token is not valid")
                return False
        return True

    @staticmethod
    def _delete_kanidm_token_from_db() -> None:
        redis.delete("kanidm:token")


class KanidmUserRepository(AbstractUserRepository):
    """
    Repository for managing users through Kanidm.
    """

    @staticmethod
    def _remove_default_groups(groups: list) -> list:
        return [item for item in groups if item not in DEFAULT_GROUPS]

    @staticmethod
    def _check_response_type_and_not_empty(data_type: str, response_data: Any) -> None:
        """
        Validates the type and that content of the response data is not empty.

        Args:
            data_type (str): Expected type of response data ('list' or 'dict').
            response_data (Any): Response data to validate.

        Raises:
            KanidmReturnEmptyResponse: If the response data is empty.
            KanidmReturnUnknownResponseType: If the response data is not of the expected type.
        """

        if not response_data or response_data is None:
            raise KanidmReturnEmptyResponse

        if data_type == "list":
            if not isinstance(response_data, list):
                raise KanidmReturnUnknownResponseType(response_data=response_data)

        elif data_type == "dict":
            if not isinstance(response_data, dict):
                raise KanidmReturnUnknownResponseType(response_data=response_data)

    @staticmethod
    def _check_user_origin_by_memberof(
        memberof: list[str] = [],
    ) -> UserDataUserOrigin:
        """
        Determines the origin of the user based on their group memberships.

        Args:
            memberof (List[str]): List of groups the user belongs to.

        Returns:
            UserDataUserOrigin: The origin type of the user (PRIMARY or NORMAL).
        """

        if all(group in memberof for group in ADMIN_GROUPS):
            return UserDataUserOrigin.PRIMARY
        else:
            return UserDataUserOrigin.NORMAL

    @staticmethod
    def _send_query(endpoint: str, method: str = "GET", data=None) -> Union[dict, list]:
        """
        Sends a request to the Kanidm API.

        Args:
            endpoint (str): The API endpoint.
            method (str, optional): The HTTP method (GET, POST, PATCH, DELETE). Defaults to "GET".
            data (Optional[dict], optional): The data to send in the request body. Defaults to None.

        Returns:
            Union[dict, list]: The response data.

        Raises:
            KanidmQueryError: If an error occurs during the request.
            UserAlreadyExists: If the user already exists.
            UserNotFound: If the user is not found.
            UserOrGroupNotFound: If the user or group does not exist.

        Raises from KanidmAdminToken:
            KanidmCliSubprocessError: If there is an error with the Kanidm CLI subprocess.
            KanidmDidNotReturnAdminPassword: If Kanidm did not return the admin password.
            FailedToGetValidKanidmToken: If a valid Kanidm token could not be retrieved.
        """

        request_method = getattr(requests, method.lower(), None)
        if not request_method:
            logger.error(f"HTTP method '{method}' is not supported.")
            raise ValueError(f"Unsupported HTTP method: {method}")

        full_endpoint = f"{KANIDM_URL}/v1/{endpoint}"

        try:
            response = request_method(
                full_endpoint,
                json=data,
                headers={
                    "Authorization": f"Bearer {KanidmAdminToken.get()}",
                    "Content-Type": "application/json",
                },
                timeout=1,
                verify=False,  # TODO: REMOVE THIS NOT HALAL!!!!!
            )
            response_data = response.json()

        except JSONDecodeError as error:
            logger.error(f"Kanidm query error: {str(error)}")
            raise KanidmQueryError(
                error_text=f"No JSON found in Kanidm response. Error: {str(error)}",
                endpoint=full_endpoint,
                method=method,
            )
        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.HTTPError,
        ) as error:
            raise KanidmQueryError(
                error_text=f"Kanidm is not responding to requests. Error: {str(error)}",
                endpoint=endpoint,
                method=method,
            )

        except Exception as error:
            logger.error(f"Kanidm query error: {str(error)}")
            raise KanidmQueryError(
                error_text=error, endpoint=full_endpoint, method=method
            )

        if response.status_code != 200:
            if isinstance(response_data, dict):
                plugin_error = response_data.get("plugin", {})
                if plugin_error.get("attrunique") == "duplicate value detected":
                    raise UserAlreadyExists  # does it work only for user? NO ONE KNOWS

            if isinstance(response_data, str):
                if response_data == "nomatchingentries":
                    raise UserOrGroupNotFound  # does it work only for user? - NO
                elif response_data == "accessdenied":
                    raise KanidmQueryError(
                        error_text="Kanidm access issue",
                        endpoint=full_endpoint,
                        method=method,
                    )
                elif response_data == "notauthenticated":
                    raise FailedToGetValidKanidmToken

            logger.error(f"Kanidm query error: {response.text}")
            raise KanidmQueryError(
                error_text=response.text, endpoint=full_endpoint, method=method
            )

        return response_data

    @staticmethod
    def create_user(
        username: str,
        directmemberof: Optional[list[str]] = None,
        displayname: Optional[str] = None,
    ) -> None:
        """
        Creates a new user.
        ! "password" is a legacy field, please use generate_password_reset_link() instead !

        Args:
            username (str): The username.
            directmemberof (Optional[List[str]], optional): List of direct group memberships. Defaults to None.
            displayname (Optional[str], optional): If displayname is None, it will default to the username.

        Raises:
            KanidmQueryError: If an error occurs while creating the user.
            UserAlreadyExists: If the user already exists.

        Raises from KanidmAdminToken:
            KanidmCliSubprocessError: If there is an error with the Kanidm CLI subprocess.
            KanidmDidNotReturnAdminPassword: If Kanidm did not return the admin password.
            FailedToGetValidKanidmToken: If a valid Kanidm token could not be retrieved.
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
        ! The root user will never return !

        Args:
            exclude_primary (bool, optional): Exclude users with PRIMARY type. Defaults to False.
            exclude_root (bool, optional): Not working for Kanidm. The root user will never return.

        Returns:
            List[UserDataUser]: The list of users.

        Raises:
            KanidmQueryError: If an error occurs while retrieving users.
            KanidmReturnUnknownResponseType: If response type is unknown.
            KanidmReturnEmptyResponse: If response is empty.

        Raises from KanidmAdminToken:
            KanidmCliSubprocessError: If there is an error with the Kanidm CLI subprocess.
            KanidmDidNotReturnAdminPassword: If Kanidm did not return the admin password.
            FailedToGetValidKanidmToken: If a valid Kanidm token could not be retrieved.
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

            directmemberof = KanidmUserRepository._remove_default_groups(groups=user_attrs.get("directmemberof", []))
            memberof = KanidmUserRepository._remove_default_groups(groups=user_attrs.get("memberof", []))

            filled_user = UserDataUser(
                username=user_attrs["name"][0],
                user_type=user_type,
                ssh_keys=[],  # actions layer will fill in this field
                directmemberof=directmemberof,
                memberof=memberof,
                displayname=user_attrs.get("displayname", [None])[0],
                email=user_attrs.get("mail", [None])[0],
            )

            users.append(filled_user)
        return users

    @staticmethod
    def delete_user(username: str) -> None:
        """
        Deletes an existing user from Kanidm.

        Args:
            username (str): The username to delete.

        Raises:
            KanidmQueryError: If an error occurs while deleting the user.
            UserNotFound: If the user does not exist.
            UserOrGroupNotFound: If the user does not exist.

        Raises from KanidmAdminToken:
            KanidmCliSubprocessError: If there is an error with the Kanidm CLI subprocess.
            KanidmDidNotReturnAdminPassword: If Kanidm did not return the admin password.
            FailedToGetValidKanidmToken: If a valid Kanidm token could not be retrieved.
        """

        KanidmUserRepository._send_query(endpoint=f"person/{username}", method="DELETE")

    @staticmethod
    def update_user(
        username: str,
        displayname: Optional[str] = None,
    ) -> None:
        """
        Update user information.
        ! Do not update the password, please use generate_password_reset_link() instead !

        Args:
            username (str): The username to update.
            directmemberof (Optional[List[str]], optional): New list of direct group memberships. Defaults to None.
            displayname (Optional[str], optional): New display name. Defaults to username if not provided.

        Raises:
            KanidmQueryError: If an error occurs while updating the user.
            UserNotFound: If the user does not exist.
            UserOrGroupNotFound: If the user or group does not exist.

        Raises from KanidmAdminToken:
            KanidmCliSubprocessError: If there is an error with the Kanidm CLI subprocess.
            KanidmDidNotReturnAdminPassword: If Kanidm did not return the admin password.
            FailedToGetValidKanidmToken: If a valid Kanidm token could not be retrieved.
        """

        data = {
            "attrs": {
                "mail": [f"{username}@{get_domain()}"],
            }
        }

        if displayname:
            data["attrs"]["displayname"] = [displayname]

        KanidmUserRepository._send_query(
            endpoint=f"person/{username}",
            method="PATCH",
            data=data,
        )

    @staticmethod
    def get_user_by_username(username: str) -> UserDataUser:
        """
        Retrieves user data by username.

        Args:
            username (str): The username to search for.

        Returns:
            UserDataUser: The user data.

        Raises:
            UserNotFound: If the user does not exist.
            UserOrGroupNotFound: If the user does not exist.
            KanidmQueryError: If an error occurs while retrieving the user data.
            KanidmReturnUnknownResponseType: If response type is unknown.

        Raises from KanidmAdminToken:
            KanidmCliSubprocessError: If there is an error with the Kanidm CLI subprocess.
            KanidmDidNotReturnAdminPassword: If Kanidm did not return the admin password.
            FailedToGetValidKanidmToken: If a valid Kanidm token could not be retrieved.
        """

        user_data = KanidmUserRepository._send_query(
            endpoint=f"person/{username}",
            method="GET",
        )

        try:
            KanidmUserRepository._check_response_type_and_not_empty(
                data_type="dict", response_data=user_data
            )
        except KanidmReturnEmptyResponse:
            raise UserNotFound

        attrs = user_data["attrs"]  # type: ignore

        directmemberof = KanidmUserRepository._remove_default_groups(groups=attrs.get("directmemberof", []))
        memberof = KanidmUserRepository._remove_default_groups(groups=attrs.get("memberof", []))

        return UserDataUser(
            username=attrs["name"][0],
            user_type=KanidmUserRepository._check_user_origin_by_memberof(
                memberof=attrs.get("memberof", [])
            ),
            ssh_keys=[],  # Actions layer will fill this field
            directmemberof=directmemberof,
            memberof=memberof,
            displayname=attrs.get("displayname", [None])[0],
            email=attrs.get("mail", [None])[0],
        )

    # ! Not implemented in JsonUserRepository !

    #           |                |
    #          \|/              \|/

    @staticmethod
    def generate_password_reset_link(username: str) -> str:
        """
        Do not reset the password, just generate a link to reset the password.
        Args:
            username (str): The username for which to generate the reset link.

        Returns:
            str: The password reset link.

        Raises:
            NoPasswordResetLinkFoundInResponse: If no token is found in the response.
            KanidmReturnEmptyResponse: If the response from Kanidm is empty.
            KanidmQueryError: If an error occurs while generating the link.
            KanidmReturnUnknownResponseType: If response type is unknown.

        Raises from KanidmAdminToken:
            KanidmCliSubprocessError: If there is an error with the Kanidm CLI subprocess.
            KanidmDidNotReturnAdminPassword: If Kanidm did not return the admin password.
            FailedToGetValidKanidmToken: If a valid Kanidm token could not be retrieved.
        """

        data = KanidmUserRepository._send_query(
            endpoint=f"person/{username}/_credential/_update_intent",
            method="GET",
        )

        KanidmUserRepository._check_response_type_and_not_empty(
            data_type="dict", response_data=data
        )

        token = data.get("token", None)  # type: ignore

        if not token:
            raise KanidmReturnEmptyResponse

        if token:
            return f"https://{KANIDM_A_RECORD}.{get_domain()}/ui/reset?token={token}"

        raise NoPasswordResetLinkFoundInResponse

    @staticmethod
    def get_groups() -> list[Group]:
        """
        Return Kanidm groups.

        Returns:
            list[Group]

        Raises:
            KanidmReturnEmptyResponse: If the response from Kanidm is empty.
            KanidmQueryError: If an error occurs while generating the link.
            KanidmReturnUnknownResponseType: If response type is unknown.

        Raises from KanidmAdminToken:
            KanidmCliSubprocessError: If there is an error with the Kanidm CLI subprocess.
            KanidmDidNotReturnAdminPassword: If Kanidm did not return the admin password.
            FailedToGetValidKanidmToken: If a valid Kanidm token could not be retrieved.
        """

        groups_list_data = KanidmUserRepository._send_query(
            endpoint="group",
            method="GET",
        )

        KanidmUserRepository._check_response_type_and_not_empty(
            data_type="list", response_data=groups_list_data
        )

        groups = []
        for group_data in groups_list_data:
            attrs = group_data.get("attrs", {})

            if "builtin" in attrs.get("class", []):
                continue

            group = Group(
                name=attrs["name"][0],
                group_class=attrs.get("class", []),
                member=attrs.get("member", []),
                memberof=attrs.get("memberof", []),
                directmemberof=attrs.get("directmemberof", []),
                spn=attrs.get("spn", [None])[0],
                description=attrs.get("description", [None])[0],
            )
            groups.append(group)

        return groups

    @staticmethod
    def add_users_to_group(users: list[str], group_name: str) -> None:
        """
        Add users to a specified group in Kanidm.

        Args:
            users (list[str]): A list of usernames to add to the group.
            group_name (str): The name of the group to which the users will be added.

        Raises:
            KanidmQueryError: If an error occurs while adding users to the group.

        Raises from KanidmAdminToken:
            KanidmCliSubprocessError: If there is an error with the Kanidm CLI subprocess.
            KanidmDidNotReturnAdminPassword: If Kanidm did not return the admin password.
            FailedToGetValidKanidmToken: If a valid Kanidm token could not be retrieved.
        """

        KanidmUserRepository._send_query(
            endpoint=f"group/{group_name}/_attr/member",
            method="POST",
            data=users,
        )

    @staticmethod
    def remove_users_from_group(users: list[str], group_name: str) -> None:
        """
        Remove users from a specified group in Kanidm.

        Args:
            users (list[str]): A list of usernames to remove from the group.
            group_name (str): The name of the group from which the users will be removed.

        Raises:
            KanidmQueryError: If an error occurs while removing users from the group.

        Raises from KanidmAdminToken:
            KanidmCliSubprocessError: If there is an error with the Kanidm CLI subprocess.
            KanidmDidNotReturnAdminPassword: If Kanidm did not return the admin password.
            FailedToGetValidKanidmToken: If a valid Kanidm token could not be retrieved.
        """

        KanidmUserRepository._send_query(
            endpoint=f"group/{group_name}/_attr/member",
            method="DELETE",
            data=users,
        )
