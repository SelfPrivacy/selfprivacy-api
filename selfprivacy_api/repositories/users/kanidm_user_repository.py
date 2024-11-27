from typing import Optional

import subprocess
import requests
import re
import logging

from selfprivacy_api.utils import get_domain, temporary_env_var
from selfprivacy_api.utils.redis_pool import RedisPool
from selfprivacy_api.models.user import UserDataUser, UserDataUserOrigin
from selfprivacy_api.repositories.users.abstract_user_repository import (
    AbstractUserRepository,
)

KANIDM_URL = "https://127.0.0.1:3013"

redis = RedisPool().get_connection()

logger = logging.getLogger(__name__)


class KanidmAdminToken:
    @staticmethod
    def get() -> str:
        kanidm_admin_token = redis.get("kanidm:token")

        if kanidm_admin_token is None:
            kanidm_admin_password = redis.get("kanidm:password")  # type: ignore

            if kanidm_admin_password is None:
                kanidm_admin_password = (
                    KanidmAdminToken.reset_and_save_idm_admin_password()
                )

            kanidm_admin_token = KanidmAdminToken.create_and_save_token(
                kanidm_admin_password=kanidm_admin_password
            )

        return kanidm_admin_token

    @staticmethod
    def create_and_save_token(kanidm_admin_password: str) -> str:
        logging.error("create_and_save_token START")

        with temporary_env_var(key="KANIDM_PASSWORD", value=kanidm_admin_password):
            subprocess.run(["kanidm", "login", "-D", "idm_admin"])

            kanidm_admin_token = subprocess.check_output(
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
            # except subprocess.CalledProcessError as e:
            #     logger.error(e)

        kanidm_admin_token = kanidm_admin_token.splitlines()[-1]

        redis.set("kanidm:token", kanidm_admin_token)
        return kanidm_admin_token

    @staticmethod
    def reset_and_save_idm_admin_password() -> str:
        logging.error("reset_and_save_idm_admin_password START")

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
        new_kanidm_admin_password = match.group(
            1
        )  # we have many not json strings in output

        redis.set("kanidm:password", new_kanidm_admin_password)
        return new_kanidm_admin_password


class KanidmQueryError(Exception):
    """Error occurred during kanidm query"""


class KanidmUserRepository(AbstractUserRepository):
    @staticmethod
    def _send_query(endpoint: str, method: str = "GET", data=None):
        request_method = getattr(requests, method.lower(), None)
        full_endpoint = f"{KANIDM_URL}/v1/{endpoint}"

        # try:
        response = request_method(
            full_endpoint,
            json=data,
            headers={
                "Authorization": f"Bearer {KanidmAdminToken.get()}",
                "Content-Type": "application/json",
            },
            timeout=0.8,  # TODO: change timeout
            verify=False,  # TODO: REMOVE THIS NOTHALAL!!!!!
        )

        if response.status_code != 200:
            raise KanidmQueryError(
                f"Kanidm returned {response.status_code} unexpected HTTP status code. Endpoint: {full_endpoint}. Error: {response.text}."
            )
        return response.json()

        # except Exception as error:
        #     raise KanidmQueryError(f"Kanidm request failed! Error: {str(error)}")

    @staticmethod
    def create_user(
        username: str,
        password: Optional[str] = None,  # TODO legacy?
        displayname: Optional[str] = None,
        email: Optional[str] = None,
        directmemberof: Optional[list[str]] = None,
        memberof: Optional[list[str]] = None,
    ) -> None:
        data = {
            "attrs": {
                "name": [username],
                "displayname": [displayname if displayname else username],
                "mail": [email if email else f"{username}@{get_domain()}"],
                "class": ["user"],  # TODO read more about it
            }
        }

        if directmemberof:
            data["attrs"]["directmemberof"] = directmemberof
        if memberof:
            data["attrs"]["memberof"] = memberof

        return KanidmUserRepository._send_query(
            endpoint="person",
            method="POST",
            data=data,
        )

    def get_users(
        exclude_primary: bool = False,
        exclude_root: bool = False,
    ) -> list[UserDataUser]:
        users_data = KanidmUserRepository._send_query(endpoint="person", method="GET")
        users = []
        for user in users_data:
            attrs = user.get("attrs", {})
            user_type = UserDataUser(
                uuid=attrs.get("uuid", [None])[0],
                username=attrs.get("name", [None])[0],
                ssh_keys=["test"],  # TODO: подключить реальные SSH-ключи
                displayname=attrs.get("displayname", [None])[0],
                email=attrs.get("mail", [None])[0],
                origin=UserDataUserOrigin.NORMAL,  # TODO
                directmemberof=attrs.get("directmemberof", []),
                memberof=attrs.get("memberof", []),
            )
            users.append(user_type)
        return users

    def delete_user(username: str) -> None:
        """Deletes an existing user"""
        return KanidmUserRepository._send_query(
            endpoint=f"person/{username}", method="DELETE"
        )

    def update_user(
        username: str,
        password: Optional[str] = None,  # TODO legacy?
        displayname: Optional[str] = None,
        email: Optional[str] = None,
        directmemberof: Optional[list[str]] = None,
        memberof: Optional[list[str]] = None,
    ) -> None:
        """Updates the password of an existing user"""

        data = {
            "attrs": {
                "displayname": [displayname if displayname else username],
                "mail": [email if email else f"{username}@{get_domain()}"],
                "class": ["user"],  # TODO read more about it
            }
        }

        if directmemberof:
            data["attrs"]["directmemberof"] = directmemberof
        if memberof:
            data["attrs"]["memberof"] = memberof

        return KanidmUserRepository._send_query(
            endpoint=f"person/{username}",
            method="PATCH",
            data=data,
        )

    def get_user_by_username(username: str) -> Optional[UserDataUser]:
        """Retrieves user data (UserDataUser) by username"""
        user_data = KanidmUserRepository._send_query(
            endpoint=f"person/{username}",
            method="GET",
        )

        if not user_data or "attrs" not in user_data:
            return None

        attrs = user_data["attrs"]

        return UserDataUser(
            uuid=attrs.get("uuid", [None])[0],
            username=attrs.get("name", [None])[0],
            displayname=attrs.get("displayname", [None])[0],
            email=attrs.get("mail", [None])[0],
            ssh_keys=attrs.get("ssh_keys", []),
            origin=UserDataUserOrigin.NORMAL,  # TODO
            directmemberof=attrs.get("directmemberof", []),
            memberof=attrs.get("memberof", []),
        )
