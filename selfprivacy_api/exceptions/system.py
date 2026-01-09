import gettext
import logging
from textwrap import dedent
from typing import Any

from selfprivacy_api.exceptions import REPORT_IT_TO_SUPPORT_CHATS
from selfprivacy_api.exceptions.abstract_exception import AbstractException
from selfprivacy_api.utils.localization import (
    DEFAULT_LOCALE,
    TranslateSystemMessage as t,
)

_ = gettext.gettext

logger = logging.getLogger(__name__)


class ShellException(AbstractException):
    """Shell command failed"""

    def __init__(self, command: str, output: Any, description: str):
        self.command = command
        self.description = description
        self.output = str(output)

        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_(
                dedent(
                    """
                    Shell command failed.
                    %(description)s
                    %(REPORT_IT_TO_SUPPORT_CHATS)s
                    Executed command: %(command)s
                    Output: %(output)s
                    """
                )
            )
            % {
                "command": self.command,
                "description": self.description,
                "output": self.output,
                "REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS,
            },
            locale=locale,
        )


class InvalidTimezone(AbstractException):
    """Invalid timezone"""

    def __init__(self, timezone: str):
        self.timezone = timezone

        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_(
                dedent(
                    """
                    Invalid timezone: %(timezone)s
                    Timezone not in pytz.all_timezones.
                    List of available timezones:
                    https://data.iana.org/time-zones/data/zone.tab
                    """
                )
            )
            % {"timezone": self.timezone},
            locale=locale,
        )


class FailedToFindResult(AbstractException):
    def __init__(self, regex_pattern: str, command: str, data: str, description: str):
        self.regex_pattern = regex_pattern
        self.command = command
        self.data = data
        self.description = description

        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_(
                dedent(
                    """
                    %(description)s
                    %(REPORT_IT_TO_SUPPORT_CHATS)s
                    Command: %(command)s
                    Used regex pattern: %(regex_pattern)s
                    Data: %(data)s
                    """
                )
            )
            % {
                "description": self.description,
                "command": self.command,
                "regex_pattern": self.regex_pattern,
                "data": self.data,
                "REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS,
            },
            locale=locale,
        )
