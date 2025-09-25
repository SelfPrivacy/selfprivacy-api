from typing import Optional
from typing import Any

from gettext import translation


class KanidmQueryError(Exception):
    """Error occurred during kanidm query"""

    def __init__(
        self,
        error_text: Optional[Any] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
    ) -> None:
        self.error_text = str(error_text)
        self.endpoint = endpoint
        self.method = method

    def get_error_message(self, locale: str) -> str:
        t = translation("messages", localedir="locales", languages=[locale])

        message = "An error occurred during the Kanidm query."
        if self.method:
            message += t.gettext(" Method: %(method)s") % {"method": self.method}
        if self.endpoint:
            message += t.gettext(" Endpoint: %(endpoint)s") % {
                "endpoint": self.endpoint
            }
        if self.error_text:
            message += t.gettext(" Error: %(error)s") % {"error": self.error_text}
        return message


class KanidmReturnEmptyResponse(Exception):
    """Kanidm returned a empty response"""

    @staticmethod
    def get_error_message(locale: str) -> str:
        t = translation("messages", localedir="locales", languages=[locale])
        return t.gettext("Kanidm returned an empty response.")


class KanidmReturnUnknownResponseType(Exception):
    """Kanidm returned a unknown response"""

    def __init__(self, response_data: Optional[Any] = None) -> None:
        self.response_data = str(response_data)

    def get_error_message(self, locale: str) -> str:
        t = translation("messages", localedir="locales", languages=[locale])
        return (
            t.gettext("Kanidm returned unknown type response. Response: %(response)s")
            % {"response": self.response_data}
            if self.response_data
            else t.gettext("Kanidm returned unknown type response.")
        )


class KanidmDidNotReturnAdminPassword(Exception):
    """Kanidm didn't return the admin password"""

    @staticmethod
    def get_error_message(locale: str) -> str:
        t = translation("messages", localedir="locales", languages=[locale])
        return t.gettext("Kanidm didn't return the admin password.")


class KanidmCliSubprocessError(Exception):
    """An error occurred when using Kanidm cli"""

    def __init__(self, error: Optional[str] = None) -> None:
        self.error = error

    def get_error_message(self, locale: str) -> str:
        t = translation("messages", localedir="locales", languages=[locale])
        return (
            t.gettext("An error occurred when using Kanidm CLI. Error: %(error)s")
            % {"error": self.error}
            if self.error
            else t.gettext("An error occurred when using Kanidm cli")
        )


class FailedToGetValidKanidmToken(Exception):
    """Kanidm failed to return a valid token"""

    @staticmethod
    def get_error_message(locale: str) -> str:
        t = translation("messages", localedir="locales", languages=[locale])
        return t.gettext("Failed to get valid Kanidm token.")
