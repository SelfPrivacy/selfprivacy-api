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
import os
from importlib.resources import files as pkg_files

from opentelemetry import trace

from selfprivacy_api.utils.singleton_metaclass import SingletonMetaclass
from selfprivacy_api.graphql.common_types.jobs import ApiJob

DEFAULT_LOCALE = "en"
_DOMAIN = "messages"
_LOCALE_DIR = pkg_files("selfprivacy_api") / "locale"
print(_LOCALE_DIR)

tracer = trace.get_tracer(__name__)


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


def get_locale(info):
    return info.context.get("locale") if info.context.get("locale") else DEFAULT_LOCALE


@tracer.start_as_current_span("translate_job")
def translate_job(job: ApiJob, locale: str) -> ApiJob:
    def _tr_opt(text: Optional[str], locale: str) -> Optional[str]:
        if text is None:
            return None
        # I did this only to maintain compatibility.
        # Why do we return empty strings instead of None at all?
        if text == "":
            return ""
        return TranslateSystemMessage.translate(text=text, locale=locale)

    return ApiJob(
        uid=job.uid,
        type_id=job.type_id,
        name=TranslateSystemMessage.translate(text=job.name, locale=locale),
        description=TranslateSystemMessage.translate(
            text=job.description, locale=locale
        ),
        status=job.status,
        status_text=_tr_opt(job.status_text, locale),
        progress=job.progress,
        created_at=job.created_at,
        updated_at=job.updated_at,
        finished_at=job.finished_at,
        error=_tr_opt(job.error, locale),
        result=_tr_opt(job.result, locale),
    )
