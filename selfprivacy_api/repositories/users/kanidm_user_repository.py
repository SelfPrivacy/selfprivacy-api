from typing import Optional

import requests

from selfprivacy_api.utils import get_domain
from selfprivacy_api.models.user import UserDataUser
from selfprivacy_api.repositories.users.abstract_user_repository import (
    AbstractUserRepository,
)

KANIDM_URL = "http://localhost:9001"
TEST_TOKEN = """eyJhbGciOiJFUzI1NiIsImtpZCI6IjVkNDUyNzdmZWUxY2UzZmNkMTViZDhkZjE3NTdlMjRkIn0.eyJhY2NvdW50X2lkIjoiYmZlN2MxNmEtNTY1NC00YzAxLWFkMjMtOWU2YjY4OTAxNDEwIiwidG9rZW5faWQiOiJmZTU5NzAxZS1iYzIyLTQwMzctYTEzNy1jZTIxYzBlNDhlZjciLCJsYWJlbCI6InRva2VuMiIsImV4cGlyeSI6bnVsbCwiaXNzdWVkX2F0IjoxNzMxMjgxMzM1LCJwdXJwb3NlIjoicmVhZHdyaXRlIn0.0fj0NAsUtBJWi1KVNKA4qi8EOHUUvaWNzeHbR82zbUVvWynnqm5ndLhFPG0v462qJXFTayonI9YJnkCaAE7a5w"""


class KanidmQueryError(Exception):
    """Error occurred during kanidm query"""

    error: str


class KanidmUserRepository(AbstractUserRepository):
    @staticmethod
    def _send_query(endpoint: str, method: str = "GET", data=None):
        request_method = getattr(requests, method.lower(), None)

        try:
            response = request_method(
                f"{KANIDM_URL}/v1/{endpoint}",
                json=data,
                headers={
                    "Authorization": f"Bearer {TEST_TOKEN}",
                    "Content-Type": "application/json",
                },
                timeout=0.8,  # TODO: change timeout
            )

            if response.status_code != 200:
                error_text = getattr(response, "text", "No response error was found...")
                raise KanidmQueryError(
                    error=f"Kanidm returned {response.status_code} unexpected HTTP status code. Error: {error_text}."
                )
            json = response.json()

            return json["data"]
        except Exception as error:
            raise KanidmQueryError(error=f"Kanidm request failed! Error: {str(error)}")

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
        return KanidmUserRepository._send_query(endpoint="person", method="GET")

    def delete_user(username: str) -> None:
        """Deletes an existing user"""
        return KanidmUserRepository._send_query()

    def update_user(username: str, password: str) -> None:
        """Updates the password of an existing user"""
        return KanidmUserRepository._send_query()

    def get_user_by_username(username: str) -> Optional[UserDataUser]:
        """Retrieves user data (UserDataUser) by username"""
        return KanidmUserRepository._send_query()
