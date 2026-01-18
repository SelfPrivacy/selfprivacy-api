import gettext
import logging
from textwrap import dedent

from selfprivacy_api.exceptions import REPORT_IT_TO_SUPPORT_CHATS
from selfprivacy_api.exceptions.abstract_exception import AbstractException
from selfprivacy_api.utils.localization import (
    DEFAULT_LOCALE,
    TranslateSystemMessage as t,
)

logger = logging.getLogger(__name__)

_ = gettext.gettext


class TokenNotFound(AbstractException):
    code = 404

    def __init__(self):
        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return (
            t.translate(
                text=_(
                    dedent(
                        """
                        Access token was not found not found.
                        %(REPORT_IT_TO_SUPPORT_CHATS)s
                        """
                    )
                ),
                locale=locale,
            )
            % {
                "REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS,
            }
        )


class RecoveryKeyNotFound(AbstractException):
    code = 404

    def __init__(self):
        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return (
            t.translate(
                text=_(
                    dedent(
                        """
                        Recovery key not found or is no longer valid.
                        %(REPORT_IT_TO_SUPPORT_CHATS)s
                        """
                    )
                ),
                locale=locale,
            )
            % {
                "REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS,
            }
        )


class InvalidMnemonic(AbstractException):
    def __init__(self):
        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_("Phrase is not mnemonic. %(REPORT_IT_TO_SUPPORT_CHATS)s"),
            locale=locale,
        ) % {
            "REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS,
        }


class NewDeviceKeyNotFound(AbstractException):
    code = 404

    def __init__(self):
        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_("New device key not found. %(REPORT_IT_TO_SUPPORT_CHATS)s"),
            locale=locale,
        ) % {
            "REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS,
        }


class CannotDeleteCallerException(AbstractException):

    def __init__(self):
        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_(
                dedent(
                    """
                    It looks like you're trying to remove access for the device you're currently using.
                    The access token you're trying to delete is active and is being used for this request,
                    so it cannot be removed.
                    %(REPORT_IT_TO_SUPPORT_CHATS)s
                    """
                )
            )
            % {"REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS},
            locale=locale,
        )


class ExpirationDateInThePast(AbstractException):

    def __init__(self):
        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_(
                dedent(
                    """
                    Specified expiration date is in the past. Please provide a future date.
                    Validation rule: expiration_date must be greater than the current time.
                    If you believe this is a mistake, there may be a problem with the server's date/time settings.
                    """
                )
            ),
            locale=locale,
        )


class InvalidUsesLeft(AbstractException):
    def __init__(self):
        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(text=_("Uses left must be greater than 0."), locale=locale)
