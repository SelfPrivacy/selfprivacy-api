"""
A localization module that loads strings from JSONs in the locale directory.
It provides a function to get a localized string by its ID.
If the string is not found in the current locale, it will try to find it in the default locale.
If the string is not found in the default locale, it will return the ID.

The locales are loaded into the memory at the api startup and kept in a singleton.
"""

from abc import ABC, abstractmethod
import gettext
from typing import Optional
from pathlib import Path
import os

from selfprivacy_api.utils.singleton_metaclass import SingletonMetaclass

DEFAULT_LOCALE = "en"
_DOMAIN = "messages"
_LOCALE_DIR = Path("/var/lib/selfprivacy-api/locale/locale")


class Localization(metaclass=SingletonMetaclass):
    """Localization class."""

    def __init__(self):
        self.supported_locales = os.listdir(str(_LOCALE_DIR))

    def get_locale(self, locale: Optional[str]) -> str:
        if not locale:
            return DEFAULT_LOCALE
        for token in locale.split(","):
            lang = token.split(";", 1)[0].strip().lower()
            base = lang.split("-", 1)[0]
            for candidate in (lang, base):
                if candidate in self.supported_locales:
                    return candidate
        return DEFAULT_LOCALE


print(
    "[i18n] .mo exists:",
    (_LOCALE_DIR / "ru" / "LC_MESSAGES" / "messages.mo").exists(),
)


class Translation(ABC):
    @staticmethod
    @abstractmethod
    def translate(locale: str, text: str) -> str:
        """Translate the message to the given locale"""
        ...


class TranslateSystemMessage(Translation):
    @staticmethod
    def translate(locale: str, text: str) -> str:
        t = gettext.translation(
            _DOMAIN, localedir=str(_LOCALE_DIR), languages=[locale], fallback=True
        )
        return t.gettext(text)
