"""Kanidm queries."""

# pylint: disable=too-few-public-methods
import requests

import strawberry

from typing import Annotated, Union

KANIDM_URL = "http://localhost:9001"


@strawberry.type
class KanidmQueryError:
    error: str


KanidmValuesResult = Annotated[
    Union[str, KanidmQueryError],  # WIP. TODO: change str
    strawberry.union("KanidmValuesResult"),
]


# WIP WIP WIP WIP WIP WIP


class KanidmQueries:
    @staticmethod
    def _send_query(query: str) -> Union[dict, KanidmQueryError]:
        try:
            response = requests.get(
                f"{KANIDM_URL}/api/v1/query",
                params={
                    "query": query,
                },
                timeout=0.8,  # TODO: change timeout
            )
            if response.status_code != 200:
                return KanidmQueryError(
                    error=f"Kanidm returned unexpected HTTP status code. Error: {response.text}. The query was {query}"
                )
            json = response.json()

            return json["data"]
        except Exception as error:
            return KanidmQueryError(error=f"Kanidm request failed! Error: {str(error)}")

    @staticmethod
    def create_user(username: str, password: str) -> KanidmValuesResult:
        query = """"""

        data = KanidmQueries._send_query(query=query)

        if isinstance(data, KanidmQueryError):
            return data

        return KanidmValuesResult(data)


# def get_users(
#     exclude_primary: bool = False,
#     exclude_root: bool = False,
# ) -> list[UserDataUser]:

# def create_user(username: str, password: str):

# def delete_user(username: str) -> None:

# def update_user(username: str, password: str) -> None:

# def get_user_by_username(username: str) -> Optional[UserDataUser]:
