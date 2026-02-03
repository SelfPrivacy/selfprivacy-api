import gettext

from selfprivacy_api.exceptions import REPORT_IT_TO_SUPPORT_CHATS
from selfprivacy_api.exceptions.abstract_exception import AbstractException
from selfprivacy_api.utils.localization import (
    DEFAULT_LOCALE,
    TranslateSystemMessage as t,
)

_ = gettext.gettext


class TokenNotFound(AbstractException):
    code = 404

    def __init__(self, log: bool = True):
        super().__init__(log=log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_("Access token was not found.\n%(REPORT_IT_TO_SUPPORT_CHATS)s"),
            locale=locale,
        ) % {
            "REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS,
        }


class RecoveryKeyNotFound(AbstractException):
    code = 404

    def __init__(self, log: bool = True):
        super().__init__(log=log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_(
                "Recovery key is not found or no longer valid.\n"
                "%(REPORT_IT_TO_SUPPORT_CHATS)s"
            ),
            locale=locale,
        ) % {
            "REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS,
        }


class InvalidMnemonic(AbstractException):
    def __init__(self, log: bool = True):
        super().__init__(log=log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_("Invalid recovery key. %(REPORT_IT_TO_SUPPORT_CHATS)s"),
            locale=locale,
        ) % {
            "REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS,
        }


class NewDeviceKeyNotFound(AbstractException):
    code = 404

    def __init__(self, log: bool = True):
        super().__init__(log=log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_("New device key not found. %(REPORT_IT_TO_SUPPORT_CHATS)s"),
            locale=locale,
        ) % {
            "REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS,
        }


class CannotDeleteCallerException(AbstractException):
    def __init__(self, log: bool = True):
        super().__init__(log=log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_(
                "The access token you’re trying to delete is currently in use by this device, so removing access is not possible.\n"
                "%(REPORT_IT_TO_SUPPORT_CHATS)s"
            )
            % {"REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS},
            locale=locale,
        )


class ExpirationDateInThePast(AbstractException):

    def __init__(self, log: bool = True):
        super().__init__(log=log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_(
                "Specified expiration date is in the past. Please provide a future date.\n"
                "If you believe this is a mistake, there may be a problem with the server's date/time settings."
            ),
            locale=locale,
        )


class InvalidUsesLeft(AbstractException):
    def __init__(self, log: bool = True):
        super().__init__(log=log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(text=_("Uses left must be greater than 0."), locale=locale)
