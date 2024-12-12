from typing import Optional
from typing import Any


class KanidmQueryError(Exception):
    """Error occurred during kanidm query"""

    def __init__(self, error_text: Optional[str] = None) -> None:
        self.error_text = error_text

    def get_error_message(self) -> str:
        return (
            f"An error occurred during the Kanidm query. Error {self.error_text}"
            if self.error_text
            else "An error occurred during the Kanidm query."
        )


class KanidmReturnEmptyResponse(Exception):
    """Kanidm returned a blank response"""

    @staticmethod
    def get_error_message() -> str:
        return "Kanidm returned an empty response."


class KanidmReturnUnknownResponseType(Exception):
    """Kanidm returned a blank response"""

    def __init__(self, response_data: Optional[Any] = None) -> None:
        self.response_data = str(response_data)

    def get_error_message(self) -> str:
        return (
            f"Kanidm returned unknown type response. Response: {self.response_data}"
            if self.response_data
            else "Kanidm returned unknown type response."
        )


class KanidmDidNotReturnAdminPassword(Exception):
    """Kanidm didn't return the admin password"""

    @staticmethod
    def get_error_message() -> str:
        return "Kanidm didn't return the admin password."


class KanidmCliSubprocessError(Exception):
    """An error occurred when using Kanidm cli"""

    def __init__(self, error: Optional[str] = None) -> None:
        self.error = error

    def get_error_message(self) -> str:
        return (
            f"An error occurred when using Kanidm cli. Error: {self.error}"
            if self.error
            else "An error occurred when using Kanidm cli."
        )


class FailedToGetValidKanidmToken(Exception):
    """Kanidm failed to return a valid token"""

    @staticmethod
    def get_error_message() -> str:
        return "Failed to get valid Kanidm token."
