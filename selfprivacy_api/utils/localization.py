"""
A localization module that loads strings from JSONs in the locale directory.
It provides a function to get a localized string by its ID.
If the string is not found in the current locale, it will try to find it in the default locale.
If the string is not found in the default locale, it will return the ID.

The locales are loaded into the memory at the api startup and kept in a singleton.
"""

from abc import ABC, abstractmethod
import gettext
import json
import os
import typing
from pathlib import Path

from selfprivacy_api.utils.singleton_metaclass import SingletonMetaclass

DEFAULT_LOCALE = "en"
_DOMAIN = "messages"
_LOCALE_DIR = Path(__file__).parent / "locales"


class Localization(metaclass=SingletonMetaclass):
    """Localization class."""

    def __init__(self):
        self.locales: typing.Dict[str, typing.Dict[str, str]] = {}
        self.load_locales()

    def load_locales(self):
        """Load locales from locale directory."""
        for locale in os.listdir(str(_LOCALE_DIR)):
            locale_path = _LOCALE_DIR / locale
            if not locale_path.is_dir():
                continue
            self.locales[locale] = {}
            for file in os.listdir(str(locale_path)):
                if file.endswith(".json"):
                    with open(locale_path / file, "r") as locale_file:
                        locale_data = self.flatten_dict(json.load(locale_file))
                        self.locales[locale].update(locale_data)

    def get(self, string_id: str, locale: str = DEFAULT_LOCALE) -> str:
        """Get localized string by its ID."""
        if locale in self.locales and string_id in self.locales[locale]:
            return self.locales[locale][string_id]
        if DEFAULT_LOCALE in self.locales and string_id in self.locales[DEFAULT_LOCALE]:
            return self.locales[DEFAULT_LOCALE][string_id]
        return string_id

    def supported_locales(self) -> typing.List[str]:
        """Return a list of supported languages."""
        return list(self.locales.keys())

    def get_locale(self, locale: typing.Optional[str]) -> str:
        """Parse the value of Accept-Language header and return the most preferred supported locale."""
        if locale is None:
            return DEFAULT_LOCALE
        for lang in locale.split(","):
            lang = lang.split(";")[0]
            if lang in self.locales:
                return lang
        return DEFAULT_LOCALE

    def flatten_dict(
        self, d: typing.Dict[str, typing.Any], parent_key: str = "", sep: str = "."
    ) -> typing.Dict[str, str]:
        """Flatten a dict."""
        items = []
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, dict):
                items.extend(self.flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)


class Translation(ABC):
    @abstractmethod
    @staticmethod
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


# class TranslateModuleMessage(Translation):
#     def translate(self, locale: str, text: str) -> str:
#         """Translate the message to the given locale"""
#         return gettext.GNUTranslations(
#             open(f"{locale}/LC_MESSAGES/messages.mo", "rb")
#         ).gettext(text)


#         ...

# class TranslateSystemMessage(Exception, Translation):
#     """An exception that has a user-facing message"""
#     service_name: str

#     def __init__(self, service_name: str):
#         self.service_name = service_name

#     def translate(self, locale: str) -> str:
#         return _("An error occurred with the service {service_name}").format(service_name=self.service_name)


# class ExceptionWithTextFromJson(Exceptioclass TranlatableMessage(ABC):
#     @abstractmethod
#     def translate(self, locale: str) -> str:
#         """Translate the message to the given locale"""
#         pass


# class ExceptionWithUserMessage(Exception, TranlatableMessage):
#     """An exception that has a user-facing message"""
#     service_name: str

#     def __init__(self, service_name: str):
#         self.service_name = service_name

#     def translate(self, locale: str) -> str:
#         return _("An error occurred with the service {service_name}").format(service_name=self.service_name)


# class ExceptionWithTextFromJson(Exception, TranlatableMessage):
#     """An exception that loads a string template from json"""
#     json_key: str
#     json_data: dict

#     def __init__(self, json_key: str, json_data: dict):
#         self.json_key = json_key
#         self.json_data = json_data

#     def translate(self, locale: str) -> str:
#         template = get_localized_string_from_sp_module(self.json_key, locale)
#         return template.format(**self.json_data)
#  n, TranlatableMessage):
#     """An exception that loads a string template from json"""
#     json_key: str
#     json_data: dict

#     def __init__(self, json_key: str, json_data: dict):
#         self.json_key = json_key
#         self.json_data = json_data

#     def translate(self, locale: str) -> str:
#         template = get_localized_string_from_sp_module(self.json_key, locale)
#         return template.format(**self.json_data)
