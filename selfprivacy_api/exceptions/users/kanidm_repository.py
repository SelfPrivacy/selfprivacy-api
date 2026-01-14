import gettext
import logging
from textwrap import dedent
from typing import Any, Optional

from selfprivacy_api.exceptions import (
    KANIDM_DEBUG_HELP,
    KANIDM_DESCRIPTION,
    KANIDM_PROBLEMS,
    REPORT_IT_TO_SUPPORT_CHATS,
)
from selfprivacy_api.exceptions.abstract_exception import AbstractException
from selfprivacy_api.utils.localization import (
    DEFAULT_LOCALE,
    TranslateSystemMessage as t,
)

_ = gettext.gettext

logger = logging.getLogger(__name__)


class KanidmQueryError(AbstractException):
    """Error occurred during kanidm query"""

    code = 500

    def __init__(
        self,
        endpoint: str,
        method: str,
        error_text: Any,
        description: Optional[str] = " ",
    ) -> None:
        self.endpoint = endpoint
        self.method = method
        self.error_text = str(error_text)
        self.description = description

        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return (
            t.translate(
                text=_(
                    dedent(
                        """
                        An error occurred while making a request to Kanidm.
                        %(KANIDM_DESCRIPTION)s
                        %(description)s
                        %(REPORT_IT_TO_SUPPORT_CHATS)s

                        Endpoint: %(endpoint)s
                        Method: %(method)s
                        Error: %(error)s
                        """
                    )
                ),
                locale=locale,
            )
            % {
                "KANIDM_DESCRIPTION": KANIDM_DESCRIPTION,
                "description": self.description,
                "REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS,
                "endpoint": self.endpoint,
                "method": self.method,
                "error": self.error_text,
            }
        )


class KanidmReturnEmptyResponse(AbstractException):
    """Kanidm returned a empty response"""

    code = 500

    def __init__(self, endpoint: str, method: str):
        self.endpoint = endpoint
        self.method = method

        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return (
            t.translate(
                text=_(
                    dedent(
                        """
                        Kanidm returned an empty response.
                        %(KANIDM_DESCRIPTION)s
                        %(REPORT_IT_TO_SUPPORT_CHATS)s

                        Endpoint: %(endpoint)s
                        Method: %(method)s
                        """
                    )
                ),
                locale=locale,
            )
            % {
                "KANIDM_DESCRIPTION": KANIDM_DESCRIPTION,
                "REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS,
                "endpoint": self.endpoint,
                "method": self.method,
            }
        )


class KanidmReturnUnknownResponseType(AbstractException):
    """Kanidm returned a unknown response"""

    code = 500

    def __init__(self, endpoint: str, method: str, response_data: Any) -> None:
        self.endpoint = endpoint
        self.method = method
        self.response_data = str(response_data)

        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return (
            t.translate(
                text=_(
                    dedent(
                        """
                        Kanidm returned unknown type response.
                        %(KANIDM_DESCRIPTION)s
                        %(KANIDM_PROBLEMS)s
                        %(REPORT_IT_TO_SUPPORT_CHATS)s

                        Endpoint %(endpoint)s
                        Method: %(method)s
                        Response: %(response)s
                        """
                    )
                ),
                locale=locale,
            )
            % {
                "KANIDM_DESCRIPTION": KANIDM_DESCRIPTION,
                "KANIDM_PROBLEMS": KANIDM_PROBLEMS,
                "REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS,
                "endpoint": self.endpoint,
                "method": self.method,
                "response": self.response_data,
            }
        )


class KanidmDidNotReturnAdminPassword(AbstractException):
    """Kanidm didn't return the admin password"""

    code = 500

    def __init__(self, command: str, regex_pattern: str, output: Any) -> None:
        self.command = command
        self.regex_pattern = regex_pattern
        self.output = str(output)

        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_(
                dedent(
                    """
                    Kanidm CLI did not return the admin password.
                    %(KANIDM_DESCRIPTION)s
                    %(KANIDM_PROBLEMS)s
                    %(REPORT_IT_TO_SUPPORT_CHATS)s

                    %(KANIDM_DEBUG_HELP)s

                    Used command: %(command)s
                    Used regex pattern: %(regex_pattern)s
                    Kanidm's CLI output: %(output)s
                    """
                )
            )
            % {
                "KANIDM_DESCRIPTION": KANIDM_DESCRIPTION,
                "KANIDM_PROBLEMS": KANIDM_PROBLEMS,
                "REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS,
                "KANIDM_DEBUG_HELP": KANIDM_DEBUG_HELP,
                "command": self.command,
                "regex_pattern": self.regex_pattern,
                "output": self.output,
            },
            locale=locale,
        )


class KanidmCliSubprocessError(AbstractException):
    """An error occurred when using Kanidm cli"""

    code = 500

    def __init__(self, command: str, description: str, error: str) -> None:
        self.command = command
        self.description = description
        self.error = error

        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_(
                dedent(
                    """
                    Kanidm CLI return error.
                    %(KANIDM_DESCRIPTION)s
                    %(description)s
                    %(KANIDM_PROBLEMS)s
                    %(REPORT_IT_TO_SUPPORT_CHATS)s

                    Used command: %(command)s
                    Error: %(error)s
                    """
                )
            )
            % {
                "KANIDM_DESCRIPTION": KANIDM_DESCRIPTION,
                "description": self.description,
                "KANIDM_PROBLEMS": KANIDM_PROBLEMS,
                "REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS,
                "command": self.command,
                "error": self.error,
            },
            locale=locale,
        )


class FailedToGetValidKanidmToken(AbstractException):
    """Kanidm failed to return a valid token"""

    code = 500

    def __init__(self):
        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return (
            t.translate(
                text=_(
                    dedent(
                        """
                        Failed to get a valid Kanidm token.
                        %(KANIDM_DESCRIPTION)s
                        %(KANIDM_PROBLEMS)s
                        %(REPORT_IT_TO_SUPPORT_CHATS)s
                        """
                    )
                ),
                locale=locale,
            )
            % {
                "KANIDM_DESCRIPTION": KANIDM_DESCRIPTION,
                "KANIDM_PROBLEMS": KANIDM_PROBLEMS,
                "REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS,
            }
        )


class NoPasswordResetLinkFoundInResponse(AbstractException):
    """No password reset link was found in the Kanidm response."""

    code = 500

    def __init__(self, endpoint: str, method: str, data: Any):
        self.endpoint = endpoint
        self.method = method
        self.data = str(data)

        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_(
                dedent(
                    """
                    The Kanidm response does not contain a password reset link.
                    %(KANIDM_DESCRIPTION)s
                    Failed to find "token" in data.
                    %(REPORT_IT_TO_SUPPORT_CHATS)s

                    Endpoint: %(endpoint)s
                    Method: %(method)s
                    Data: %(data)s
                    """
                )
                % {
                    "KANIDM_DESCRIPTION": KANIDM_DESCRIPTION,
                    "REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS,
                    "endpoint": self.endpoint,
                    "method": self.method,
                    "data": self.data,
                }
            ),
            locale=locale,
        )
