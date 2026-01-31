import gettext
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


class KanidmQueryError(AbstractException):
    """Error occurred during kanidm query"""

    code = 500

    def __init__(
        self,
        endpoint: str,
        method: str,
        error_text: Any,
        description: Optional[str] = " ",
        log: bool = True,
    ) -> None:
        self.endpoint = endpoint
        self.method = method
        self.error_text = str(error_text)
        self.description = description

        super().__init__(log=log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_(
                "An error occurred during a request to Kanidm.\n"
                "%(KANIDM_DESCRIPTION)s\n"
                "%(description)s\n"
                "%(REPORT_IT_TO_SUPPORT_CHATS)s\n"
                "\n"
                "Endpoint: %(endpoint)s\n"
                "Method: %(method)s\n"
                "Error: %(error)s"
            ),
            locale=locale,
        ) % {
            "KANIDM_DESCRIPTION": KANIDM_DESCRIPTION,
            "description": self.description,
            "REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS,
            "endpoint": self.endpoint,
            "method": self.method,
            "error": self.error_text,
        }


class KanidmReturnEmptyResponse(AbstractException):
    """Kanidm returned an empty response"""

    code = 500

    def __init__(
        self,
        endpoint: str,
        method: str,
        log: bool = True,
    ):
        self.endpoint = endpoint
        self.method = method

        super().__init__(log=log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_(
                "Kanidm returned an empty response.\n"
                "%(KANIDM_DESCRIPTION)s\n"
                "%(REPORT_IT_TO_SUPPORT_CHATS)s\n\n"
                "Endpoint: %(endpoint)s\n"
                "Method: %(method)s"
            ),
            locale=locale,
        ) % {
            "KANIDM_DESCRIPTION": KANIDM_DESCRIPTION,
            "REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS,
            "endpoint": self.endpoint,
            "method": self.method,
        }


class KanidmReturnUnknownResponseType(AbstractException):
    """Kanidm returned an unknown response"""

    code = 500

    def __init__(
        self,
        endpoint: str,
        method: str,
        response_data: Any,
        log: bool = True,
    ) -> None:
        self.endpoint = endpoint
        self.method = method
        self.response_data = str(response_data)

        super().__init__(log=log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_(
                "Kanidm returned an unknown type response.\n"
                "%(KANIDM_DESCRIPTION)s\n"
                "%(KANIDM_PROBLEMS)s\n"
                "%(REPORT_IT_TO_SUPPORT_CHATS)s\n\n"
                "Endpoint: %(endpoint)s\n"
                "Method: %(method)s\n"
                "Response: %(response)s"
            ),
            locale=locale,
        ) % {
            "KANIDM_DESCRIPTION": KANIDM_DESCRIPTION,
            "KANIDM_PROBLEMS": KANIDM_PROBLEMS,
            "REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS,
            "endpoint": self.endpoint,
            "method": self.method,
            "response": self.response_data,
        }


class KanidmDidNotReturnAdminPassword(AbstractException):
    """Kanidm didn't return the admin password"""

    code = 500

    def __init__(
        self,
        command: str,
        regex_pattern: str,
        output: Any,
        log: bool = True,
    ) -> None:
        self.command = command
        self.regex_pattern = regex_pattern
        self.output = str(output)

        super().__init__(log=log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_(
                "Failed to get access to Kanidm admin account:\n"
                "Kanidm CLI did not reset the admin password.\n"
                "%(KANIDM_DESCRIPTION)s\n"
                "%(KANIDM_PROBLEMS)s\n"
                "%(REPORT_IT_TO_SUPPORT_CHATS)s\n\n"
                "%(KANIDM_DEBUG_HELP)s\n\n"
                "Used command: %(command)s\n"
                "Used regex pattern: %(regex_pattern)s\n"
                "Kanidm's CLI output: %(output)s"
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

    def __init__(
        self,
        command: str,
        error: str,
        description: str = _("Error creating Kanidm token"),
        log: bool = True,
    ) -> None:
        self.command = command
        self.description = description
        self.error = error

        super().__init__(log=log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_(
                "Kanidm CLI returned an error.\n"
                "%(KANIDM_DESCRIPTION)s\n"
                "%(description)s\n"
                "%(KANIDM_PROBLEMS)s\n"
                "%(REPORT_IT_TO_SUPPORT_CHATS)s\n\n"
                "Used command: %(command)s\n"
                "Error: %(error)s"
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
    """Сouldn't get a valid Kanidm token"""

    code = 500

    def __init__(self, log: bool = True):
        super().__init__(log=log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_(
                "Сouldn't get a valid Kanidm token.\n"
                "%(KANIDM_DESCRIPTION)s\n"
                "%(KANIDM_PROBLEMS)s\n"
                "%(REPORT_IT_TO_SUPPORT_CHATS)s"
            ),
            locale=locale,
        ) % {
            "KANIDM_DESCRIPTION": KANIDM_DESCRIPTION,
            "KANIDM_PROBLEMS": KANIDM_PROBLEMS,
            "REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS,
        }


class NoPasswordResetLinkFoundInResponse(AbstractException):
    """Kanidm didn't return a password reset link"""

    code = 500

    def __init__(
        self,
        endpoint: str,
        method: str,
        data: Any,
        log: bool = True,
    ):
        self.endpoint = endpoint
        self.method = method
        self.data = str(data)

        super().__init__(log=log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_(
                "Kanidm didn't return a password reset link.\n"
                "%(KANIDM_DESCRIPTION)s\n"
                'Failed to find "token" in data.\n'
                "%(REPORT_IT_TO_SUPPORT_CHATS)s\n\n"
                "Endpoint: %(endpoint)s\n"
                "Method: %(method)s\n"
                "Data: %(data)s\n"
            )
            % {
                "KANIDM_DESCRIPTION": KANIDM_DESCRIPTION,
                "REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS,
                "endpoint": self.endpoint,
                "method": self.method,
                "data": self.data,
            },
            locale=locale,
        )
