import gettext
import logging

from selfprivacy_api.utils.localization import (
    DEFAULT_LOCALE,
    TranslateSystemMessage as t,
)
from selfprivacy_api.utils.strings import REPORT_IT_TO_SUPPORT_CHATS

logger = logging.getLogger(__name__)

_ = gettext.gettext


class TokenNotFound(Exception):
    def __init__(self):
        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_("Token not found. %(REPORT_IT_TO_SUPPORT_CHATS)s"),
            locale=locale,
        ) % {
            "REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS,
        }


class RecoveryKeyNotFound(Exception):
    def __init__(self):
        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_("Recovery key not found. %(REPORT_IT_TO_SUPPORT_CHATS)s"),
            locale=locale,
        ) % {
            "REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS,
        }


class InvalidMnemonic(Exception):
    def __init__(self):
        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_("Phrase is not mnemonic. %(REPORT_IT_TO_SUPPORT_CHATS)s"),
            locale=locale,
        ) % {
            "REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS,
        }


class NewDeviceKeyNotFound(Exception):
    def __init__(self):
        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_("New device key not found. %(REPORT_IT_TO_SUPPORT_CHATS)s"),
            locale=locale,
        ) % {
            "REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS,
        }
