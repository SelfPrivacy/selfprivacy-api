import gettext
import logging
from textwrap import dedent

from selfprivacy_api.models.exception import ApiException
from selfprivacy_api.utils.localization import (
    DEFAULT_LOCALE,
    TranslateSystemMessage as t,
)
from selfprivacy_api.utils.strings import REPORT_IT_TO_SUPPORT_CHATS

logger = logging.getLogger(__name__)

_ = gettext.gettext


class TokenNotFound(ApiException):
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


class RecoveryKeyNotFound(ApiException):
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
                        %(REPORT_IT_TO_SUPPORT_CHATS)s")
                        """
                    )
                ),
                locale=locale,
            )
            % {
                "REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS,
            }
        )


class InvalidMnemonic(ApiException):
    code = 400

    def __init__(self):
        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_("Phrase is not mnemonic. %(REPORT_IT_TO_SUPPORT_CHATS)s"),
            locale=locale,
        ) % {
            "REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS,
        }


class NewDeviceKeyNotFound(ApiException):
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


TOKEN_EXCEPTIONS = (
    TokenNotFound,
    RecoveryKeyNotFound,
    InvalidMnemonic,
    NewDeviceKeyNotFound,
)
