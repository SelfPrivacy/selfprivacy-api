from typing import Optional

import requests

from selfprivacy_api.utils import get_domain
from selfprivacy_api.models.user import UserDataUser, UserDataUserOrigin
from selfprivacy_api.repositories.users.abstract_user_repository import (
    AbstractUserRepository,
)

KANIDM_URL = "https://127.0.0.1:3013"
TEST_TOKEN = """eyJhbGciOiJFUzI1NiIsImtpZCI6IjVkNDUyNzdmZWUxY2UzZmNkMTViZDhkZjE3NTdlMjRkIn0.eyJhY2NvdW50X2lkIjoiYmZlN2MxNmEtNTY1NC00YzAxLWFkMjMtOWU2YjY4OTAxNDEwIiwidG9rZW5faWQiOiJmZTU5NzAxZS1iYzIyLTQwMzctYTEzNy1jZTIxYzBlNDhlZjciLCJsYWJlbCI6InRva2VuMiIsImV4cGlyeSI6bnVsbCwiaXNzdWVkX2F0IjoxNzMxMjgxMzM1LCJwdXJwb3NlIjoicmVhZHdyaXRlIn0.0fj0NAsUtBJWi1KVNKA4qi8EOHUUvaWNzeHbR82zbUVvWynnqm5ndLhFPG0v462qJXFTayonI9YJnkCaAE7a5w"""


class KanidmQueryError(Exception):
    """Error occurred during kanidm query"""


class KanidmUserRepository(AbstractUserRepository):
    @staticmethod
    def _send_query(endpoint: str, method: str = "GET", data=None):
        request_method = getattr(requests, method.lower(), None)
        full_endpoint = f"{KANIDM_URL}/v1/{endpoint}"

        try:
            response = request_method(
                full_endpoint,
                json=data,
                headers={
                    "Authorization": f"Bearer {TEST_TOKEN}",
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

        except Exception as error:
            raise KanidmQueryError(f"Kanidm request failed! Error: {str(error)}")

    @staticmethod
    def create_user(username: str, password: str):
        data = {
            "attrs": {
                "name": [username],
                "displayname": [username],
                "mail": [f"{username}@{get_domain()}"],
                "class": ["user"],
            }
        }

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
                ssh_keys=["test"],  # TODO
                displayname=attrs.get("displayname", [None])[0],
                email=attrs.get("mail", [None])[0],
                origin=UserDataUserOrigin.NORMAL,  # TODO
            )
            users.append(user_type)
        return users

    def delete_user(username: str) -> None:
        """Deletes an existing user"""
        return KanidmUserRepository._send_query()

    def update_user(username: str, password: str) -> None:
        """Updates the password of an existing user"""
        return KanidmUserRepository._send_query()

    def get_user_by_username(username: str) -> Optional[UserDataUser]:
        """Retrieves user data (UserDataUser) by username"""
        return KanidmUserRepository._send_query()
