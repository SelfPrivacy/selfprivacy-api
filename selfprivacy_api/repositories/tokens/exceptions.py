import gettext

from selfprivacy_api.utils.localization import TranslateSystemMessage as t

_ = gettext.gettext


class TokenNotFound(Exception):
    @staticmethod
    def get_error_message(locale: str) -> str:
        return t.translate(text=_("Token not found"), locale=locale)


class RecoveryKeyNotFound(Exception):
    @staticmethod
    def get_error_message(locale: str) -> str:
        return t.translate(text=_("Recovery key not found"), locale=locale)


class InvalidMnemonic(Exception):
    @staticmethod
    def get_error_message(locale: str) -> str:
        return t.translate(text=_("Phrase is not mnemonic"), locale=locale)


class NewDeviceKeyNotFound(Exception):
    @staticmethod
    def get_error_message(locale: str) -> str:
        return t.translate(text=_("New device key not found"), locale=locale)
