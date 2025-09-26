from typing import Optional
from typing import Any

import gettext

from selfprivacy_api.utils.localization import TranslateSystemMessage as t

_ = gettext.gettext


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
        message = t.translate(
            text=_("An error occurred during the Kanidm query."), locale=locale
        )
        if self.method:
            message += t.translate(text=_(" Method: %(method)s"), locale=locale) % {
                "method": self.method
            }
        if self.endpoint:
            message += t.translate(text=_(" Endpoint: %(endpoint)s"), locale=locale) % {
                "endpoint": self.endpoint
            }
        if self.error_text:
            message += t.translate(text=_(" Error: %(error)s"), locale=locale) % {
                "error": self.error_text
            }
        return message


class KanidmReturnEmptyResponse(Exception):
    """Kanidm returned a empty response"""

    @staticmethod
    def get_error_message(locale: str) -> str:
        return t.translate(text=_("Kanidm returned an empty response."), locale=locale)


class KanidmReturnUnknownResponseType(Exception):
    """Kanidm returned a unknown response"""

    def __init__(self, response_data: Optional[Any] = None) -> None:
        self.response_data = str(response_data)

    def get_error_message(self, locale: str) -> str:
        return (
            t.translate(
                text=_("Kanidm returned unknown type response. Response: %(response)s"),
                locale=locale,
            )
            % {"response": self.response_data}
            if self.response_data
            else t.translate(
                text=_("Kanidm returned unknown type response."), locale=locale
            )
        )


class KanidmDidNotReturnAdminPassword(Exception):
    """Kanidm didn't return the admin password"""

    @staticmethod
    def get_error_message(locale: str) -> str:
        return t.translate(
            text=_("Kanidm didn't return the admin password."), locale=locale
        )


class KanidmCliSubprocessError(Exception):
    """An error occurred when using Kanidm cli"""

    def __init__(self, error: Optional[str] = None) -> None:
        self.error = error

    def get_error_message(self, locale: str) -> str:
        return t.translate(
            text=_("An error occurred when using Kanidm CLI. Error: %(error)s"),
            locale=(
                locale % {"error": self.error}
                if self.error
                else t.translate(
                    text=_("An error occurred when using Kanidm cli"), locale=locale
                )
            ),
        )


class FailedToGetValidKanidmToken(Exception):
    """Kanidm failed to return a valid token"""

    @staticmethod
    def get_error_message(locale: str) -> str:
        return t.translate(text=_("Failed to get valid Kanidm token."), locale=locale)
