import gettext

from selfprivacy_api.exceptions import REPORT_IT_TO_SUPPORT_CHATS
from selfprivacy_api.exceptions.abstract_exception import AbstractException
from selfprivacy_api.utils.localization import (
    DEFAULT_LOCALE,
    TranslateSystemMessage as t,
)

_ = gettext.gettext


class DbusCallFailed(AbstractException):
    """D-Bus call failed"""

    code = 500

    def __init__(
        self,
        error: Exception,
        operation: str,
        log: bool = True,
    ):
        self.error = str(error)
        self.error_name = getattr(error, "dbus_error_name", None) or "unknown"
        self.operation = operation

        super().__init__(log=log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_(
                "D-Bus call failed.\n"
                "Operation: %(operation)s\n"
                "D-Bus error: %(error_name)s\n"
                "%(REPORT_IT_TO_SUPPORT_CHATS)s\n"
                "Error: %(error)s"
            ),
            locale=locale,
        ) % {
            "operation": self.operation,
            "error_name": self.error_name,
            "error": self.error,
            "REPORT_IT_TO_SUPPORT_CHATS": t.translate(
                text=REPORT_IT_TO_SUPPORT_CHATS, locale=locale
            ),
        }
