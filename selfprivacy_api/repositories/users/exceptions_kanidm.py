from typing import Optional


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

    @staticmethod
    def get_error_message() -> str:
        return "Kanidm returned an empty response."


class KanidmDidNotReturnAdminPassword(Exception):
    """Kanidm didn't return the admin password"""

    @staticmethod
    def get_error_message() -> str:
        return "Kanidm didn't return the admin password."
