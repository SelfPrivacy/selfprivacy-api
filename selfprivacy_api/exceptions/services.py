import gettext
import logging

from selfprivacy_api.exceptions import REPORT_IT_TO_SUPPORT_CHATS
from selfprivacy_api.exceptions.abstract_exception import AbstractException
from selfprivacy_api.utils.localization import (
    DEFAULT_LOCALE,
    TranslateSystemMessage as t,
)

_ = gettext.gettext

logger = logging.getLogger(__name__)


class ServiceNotFoundError(AbstractException):
    code = 404

    def __init__(self, service_id: str, log: bool = True):
        self.service_id = service_id

        super().__init__(log=log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_("No such service: %(service_id)s. %(REPORT_IT_TO_SUPPORT_CHATS)s"),
            locale=locale,
        ) % {
            "service_id": self.service_id,
            "REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS,
        }


class VolumeNotFoundError(AbstractException):
    code = 404

    def __init__(self, volume_name: str, log: bool = True):
        self.volume_name = volume_name

        super().__init__(log=log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_("No such volume: %(volume_name)s. %(REPORT_IT_TO_SUPPORT_CHATS)s"),
            locale=locale,
        ) % {
            "volume_name": self.volume_name,
            "REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS,
        }
