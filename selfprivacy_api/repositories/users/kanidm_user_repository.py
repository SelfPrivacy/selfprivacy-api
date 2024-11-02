from typing import Optional

import requests

from selfprivacy_api.models.user import UserDataUser
from selfprivacy_api.repositories.users.abstract_user_repository import (
    AbstractUserRepository,
)

KANIDM_URL = "http://localhost:9001"


class KanidmQueryError(Exception):
    """Error occurred during Kanidm query"""


class KanidmUserRepository(AbstractUserRepository):
    @staticmethod
    def _send_query(endpoint: str, method: str = "GET", **kwargs):
        request_method = getattr(requests, method.lower(), None)

        try:
            response = request_method(
                f"{KANIDM_URL}/api/v1/{endpoint}",
                params=kwargs,
                timeout=0.8,  # TODO: change timeout
            )

            if response.status_code != 200:
                raise KanidmQueryError(
                    error=f"Kanidm returned unexpected HTTP status code. Error: {response.text}."
                )
            json = response.json()

            return json["data"]
        except Exception as error:
            raise KanidmQueryError(error=f"Kanidm request failed! Error: {str(error)}")

    @staticmethod
    def create_user(username: str, password: str):
        return KanidmUserRepository._send_query(
            endpoint="person", method="POST", name=username, displayname=username
        )

    def get_users(
        exclude_primary: bool = False,
        exclude_root: bool = False,
    ) -> list[UserDataUser]:
        return KanidmUserRepository._send_query()

    def delete_user(username: str) -> None:
        """Deletes an existing user"""
        return KanidmUserRepository._send_query()

    def update_user(username: str, password: str) -> None:
        """Updates the password of an existing user"""
        return KanidmUserRepository._send_query()

    def get_user_by_username(username: str) -> Optional[UserDataUser]:
        """Retrieves user data (UserDataUser) by username"""
        return KanidmUserRepository._send_query()
