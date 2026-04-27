import gettext
import logging
from typing import Optional

from selfprivacy_api.exceptions.users import (
    UserNotFound,
)
from selfprivacy_api.exceptions.users.kanidm_repository import (
    KanidmReturnEmptyResponse,
    NoPasswordResetLinkFoundInResponse,
)
from selfprivacy_api.models.group import Group, get_default_grops
from selfprivacy_api.models.user import UserDataUser, UserDataUserOrigin
from selfprivacy_api.repositories.users.abstract_user_repository import (
    AbstractUserRepository,
)
from selfprivacy_api.services import KANIDM_A_RECORD
from selfprivacy_api.utils import get_domain
from selfprivacy_api.utils.kanidm import check_kanidm_response_type, send_kanidm_query

SP_ADMIN_GROUPS = ["sp.admins"]
SP_DEFAULT_GROUPS = ["sp.full_users"]


logger = logging.getLogger(__name__)

_ = gettext.gettext


class KanidmUserRepository(AbstractUserRepository):
    """
    Repository for managing users through Kanidm.
    """

    @staticmethod
    def _remove_default_groups(groups: list) -> list:
        return [item for item in groups if item not in get_default_grops()]

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

        if all(group in memberof for group in SP_ADMIN_GROUPS):
            return UserDataUserOrigin.PRIMARY
        else:
            return UserDataUserOrigin.NORMAL

    @staticmethod
    async def create_user(
        username: str,
        directmemberof: Optional[list[str]] = None,
        displayname: Optional[str] = None,
        password: Optional[str] = None,
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
                "class": ["user"],
            }
        }

        await send_kanidm_query(
            endpoint="person",
            method="POST",
            data=data,
        )

        if directmemberof:
            for group in directmemberof:
                await KanidmUserRepository.add_users_to_group(
                    users=[username],
                    group_name=group,
                )

    @staticmethod
    async def get_users(
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

        endpoint = "person"
        method = "GET"
        users_data = await send_kanidm_query(endpoint=endpoint, method=method)

        check_kanidm_response_type(
            data_type="list",
            response_data=users_data,
            endpoint=endpoint,
            method=method,
        )

        users = []
        for user in users_data:
            user_attrs = user.get("attrs", {})

            user_type = KanidmUserRepository._check_user_origin_by_memberof(
                memberof=[
                    group.rsplit("@")[0] for group in user_attrs.get("memberof", [])
                ]
            )
            if exclude_primary and user_type == UserDataUserOrigin.PRIMARY:
                continue

            directmemberof = KanidmUserRepository._remove_default_groups(
                groups=[
                    group.rsplit("@")[0]
                    for group in user_attrs.get("directmemberof", [])
                ]
            )
            memberof = KanidmUserRepository._remove_default_groups(
                groups=[
                    group.rsplit("@")[0] for group in user_attrs.get("memberof", [])
                ]
            )

            filled_user = UserDataUser(
                username=user_attrs["name"][0],
                user_type=user_type,
                ssh_keys=[],  # actions layer will fill in this field
                directmemberof=directmemberof,
                memberof=memberof,
                display_name=user_attrs.get("displayname", [None])[0],
                email=user_attrs.get("mail", [None])[0],
            )

            users.append(filled_user)
        return users

    @staticmethod
    async def delete_user(username: str) -> None:
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

        await send_kanidm_query(endpoint=f"person/{username}", method="DELETE")

    @staticmethod
    async def update_user(
        username: str,
        displayname: Optional[str] = None,
        password: Optional[str] = None,
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

        await send_kanidm_query(
            endpoint=f"person/{username}",
            method="PATCH",
            data=data,
        )

    @staticmethod
    async def get_user_by_username(username: str) -> UserDataUser:
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

        endpoint = f"person/{username}"
        method = "GET"
        user_data = await send_kanidm_query(
            endpoint=endpoint,
            method=method,
        )

        try:
            check_kanidm_response_type(
                data_type="dict",
                endpoint=endpoint,
                method=method,
                response_data=user_data,
            )
        except KanidmReturnEmptyResponse:
            raise UserNotFound

        attrs = user_data["attrs"]  # type: ignore

        directmemberof = KanidmUserRepository._remove_default_groups(
            groups=[group.rsplit("@")[0] for group in attrs.get("directmemberof", [])]
        )
        memberof = KanidmUserRepository._remove_default_groups(
            groups=[group.rsplit("@")[0] for group in attrs.get("memberof", [])]
        )

        return UserDataUser(
            username=attrs["name"][0],
            user_type=KanidmUserRepository._check_user_origin_by_memberof(
                memberof=[group.rsplit("@")[0] for group in attrs.get("memberof", [])]
            ),
            ssh_keys=[],  # Actions layer will fill this field
            directmemberof=directmemberof,
            memberof=memberof,
            display_name=attrs.get("displayname", [None])[0],
            email=attrs.get("mail", [None])[0],
        )

    # ! Not implemented in JsonUserRepository !

    #           |                |
    #          \|/              \|/

    @staticmethod
    async def generate_password_reset_link(username: str) -> str:
        """
        Do not reset the password, just generate a link to reset the password.
        Args:
            username (str): The username for which to generate the reset link.

        Returns:
            str: The password reset link.

        Raises:
            NoPasswordResetLinkFoundInResponse: If no token is found in the response.
            KanidmQueryError: If an error occurs while generating the link.
            KanidmReturnUnknownResponseType: If response type is unknown.

        Raises from KanidmAdminToken:
            KanidmCliSubprocessError: If there is an error with the Kanidm CLI subprocess.
            KanidmDidNotReturnAdminPassword: If Kanidm did not return the admin password.
            FailedToGetValidKanidmToken: If a valid Kanidm token could not be retrieved.
        """

        method = "GET"
        endpoint = f"person/{username}/_credential/_update_intent"
        data = await send_kanidm_query(
            endpoint=endpoint,
            method=method,
        )

        check_kanidm_response_type(
            endpoint=endpoint,
            method=method,
            data_type="dict",
            response_data=data,
        )

        token = data.get("token", None)  # type: ignore

        if token:
            return f"https://{KANIDM_A_RECORD}.{get_domain()}/ui/reset?token={token}"

        raise NoPasswordResetLinkFoundInResponse(
            endpoint=endpoint, method=method, data=data
        )

    @staticmethod
    async def get_groups() -> list[Group]:
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

        endpoint = "group"
        method = "GET"
        groups_list_data = await send_kanidm_query(
            endpoint=endpoint,
            method=method,
        )

        check_kanidm_response_type(
            endpoint=endpoint,
            method=method,
            data_type="list",
            response_data=groups_list_data,
        )

        groups = []
        for group_data in groups_list_data:
            attrs = group_data.get("attrs", {})

            if "builtin" in attrs.get("class", []):
                continue

            if attrs.get("name", [None])[0] in ["ext_idm_provisioned_entities"]:
                continue

            group = Group(
                name=attrs["name"][0],
                group_class=attrs.get("class", []),
                member=[user.rsplit("@")[0] for user in attrs.get("member", [])],
                memberof=[group.rsplit("@")[0] for group in attrs.get("memberof", [])],
                directmemberof=[
                    group.rsplit("@")[0] for group in attrs.get("directmemberof", [])
                ],
                spn=attrs.get("spn", [None])[0],
                description=attrs.get("description", [None])[0],
            )
            groups.append(group)

        return groups

    @staticmethod
    async def add_users_to_group(users: list[str], group_name: str) -> None:
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

        await send_kanidm_query(
            endpoint=f"group/{group_name}/_attr/member",
            method="POST",
            data=users,
        )

    @staticmethod
    async def remove_users_from_group(users: list[str], group_name: str) -> None:
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

        await send_kanidm_query(
            endpoint=f"group/{group_name}/_attr/member",
            method="DELETE",
            data=users,
        )
