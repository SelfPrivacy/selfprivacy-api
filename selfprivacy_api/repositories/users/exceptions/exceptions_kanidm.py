from typing import Any, Optional, Union
from textwrap import dedent
import gettext
import logging

from selfprivacy_api.utils.localization import (
    DEFAULT_LOCALE,
    TranslateSystemMessage as t,
)

_ = gettext.gettext

logger = logging.getLogger(__name__)

KANIDM_BROKE_COMPATIBILITY = (
    "There may have been a Kanidm update that broke compatibility."
)


class KanidmQueryError(Exception):
    """Error occurred during kanidm query"""

    def __init__(
        self,
        endpoint: str,
        method: str,
        error_text: Any,
        description: Optional[str] = KANIDM_BROKE_COMPATIBILITY,
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
                        Something went wrong while querying the Kanidm user management program.
                        %(description)s
                        Commands to debug:
                          "systemctl status kanidm.service"
                          "journalctl -u kanidm.service -f"
                        Endpoint: %(endpoint)s.
                        Method: %(method)s.
                        Error: %(error)s
                        """
                    )
                ),
                locale=locale,
            )
            % {
                "endpoint": self.endpoint,
                "method": self.method,
                "error": self.error_text,
                "description": self.description,
            }
        )


class KanidmReturnEmptyResponse(Exception):
    """Kanidm returned a empty response"""

    def __init__(self):
        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(text=_("Kanidm returned an empty response."), locale=locale)


class KanidmReturnUnknownResponseType(Exception):
    """Kanidm returned a unknown response"""

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
                        Something is wrong with the user management program Kanidm.
                        Kanidm returned unknown type response.
                        There may have been a Kanidm update that broke compatibility.
                        Endpoint %(endpoint)s.
                        Method: %(method)s.
                        Response: %(response)s.
                        """
                    )
                ),
                locale=locale,
            )
            % {
                "endpoint": self.endpoint,
                "method": self.method,
                "response": self.response_data,
            }
        )


class KanidmDidNotReturnAdminPassword(Exception):
    """Kanidm didn't return the admin password"""

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
                    Something is wrong with the user management program Kanidm.
                    Kanidm CLI did not return the admin password.
                    %(maybe_kanidm_broke_compatibility)s
                    Used command: %(command)s
                    Used regex pattern: %(regex_pattern)s
                    Kanidm's CLI output: %(output)s
                    """
                )
            )
            % {
                "command": self.command,
                "regex_pattern": self.regex_pattern,
                "output": self.output,
                "maybe_kanidm_broke_compatibility": KANIDM_BROKE_COMPATIBILITY,
            },
            locale=locale,
        )


class KanidmCliSubprocessError(Exception):
    """An error occurred when using Kanidm cli"""

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
                    %(description)s
                    Something is wrong with the user management program Kanidm.
                    Kanidm CLI return error.
                    %(maybe_kanidm_broke_compatibility)s
                    Used command: %(command)s
                    Error: %(error)s
                    """
                )
            )
            % {
                "command": self.command,
                "description": self.description,
                "error": self.error,
                "maybe_kanidm_broke_compatibility": KANIDM_BROKE_COMPATIBILITY,
            },
            locale=locale,
        )


class FailedToGetValidKanidmToken(Exception):
    """Kanidm failed to return a valid token"""

    def __init__(self):
        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(text=_("Failed to get valid Kanidm token."), locale=locale)


class NoPasswordResetLinkFoundInResponse(Exception):
    """No password reset link was found in the Kanidm response."""

    def __init__(self, endpoint: str, method: str, data: Union[dict, list]):
        self.endpoint = endpoint
        self.method = method
        self.data = data

        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_(
                dedent(
                    """
                    The Kanidm response does not contain a password reset link.
                    Failed to find "token" in data.
                    Endpoint: %(endpoint)s
                    Method: %(method)s
                    Data: %(data)s
                    """
                )
                % {
                    "endpoint": self.endpoint,
                    "method": self.method,
                    "data": self.data,
                }
            ),
            locale=locale,
        )
