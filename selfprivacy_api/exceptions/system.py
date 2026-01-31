import gettext
from typing import Any

from selfprivacy_api.exceptions import REPORT_IT_TO_SUPPORT_CHATS
from selfprivacy_api.exceptions.abstract_exception import AbstractException
from selfprivacy_api.utils.localization import (
    DEFAULT_LOCALE,
    TranslateSystemMessage as t,
)

_ = gettext.gettext


class ShellException(AbstractException):
    """Shell command failed"""

    def __init__(
        self,
        command: str,
        output: Any,
        description: str,
        log: bool = True,
    ):
        self.command = command
        self.description = description
        self.output = str(output)

        super().__init__(log=log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_(
                "Shell command failed.\n"
                "%(description)s\n"
                "%(REPORT_IT_TO_SUPPORT_CHATS)s\n"
                "Executed command: %(command)s\n"
                "Output: %(output)s"
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

    def __init__(self, timezone: str, log: bool = True):
        self.timezone = timezone

        super().__init__(log=log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_(
                "Invalid timezone: %(timezone)s\n"
                "Timezone not in pytz.all_timezones.\n"
                "List of available timezones:\n"
                "https://data.iana.org/time-zones/data/zone.tab"
            )
            % {"timezone": self.timezone},
            locale=locale,
        )


class FailedToFindResult(AbstractException):
    def __init__(
        self,
        regex_pattern: str,
        command: str,
        data: str,
        description: str,
        log: bool = True,
    ):
        self.regex_pattern = regex_pattern
        self.command = command
        self.data = data
        self.description = description

        super().__init__(log=log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_(
                "%(description)s\n"
                "%(REPORT_IT_TO_SUPPORT_CHATS)s\n"
                "Command: %(command)s\n"
                "Used regex pattern: %(regex_pattern)s\n"
                "Data: %(data)s"
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
