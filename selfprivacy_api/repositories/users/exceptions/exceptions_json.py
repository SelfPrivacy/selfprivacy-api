import gettext
import logging
from textwrap import dedent

from selfprivacy_api.utils import USERDATA_FILE
from selfprivacy_api.utils.localization import (
    DEFAULT_LOCALE,
    TranslateSystemMessage as t,
)
from selfprivacy_api.utils.strings import REPORT_IT_TO_SUPPORT_CHATS

_ = gettext.gettext

logger = logging.getLogger(__name__)


class PrimaryUserNotFoundInJsonUserData(Exception):
    """Invalid configuration, userdata is broken"""

    def __init__(self):
        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_(
                dedent(
                    """
                    Invalid UserData configuration.
                    Failed to find "username" in %(path_to_file)s.
                    %(REPORT_IT_TO_SUPPORT_CHATS)s
                    """
                )
            )
            % {
                "path_to_file": USERDATA_FILE,
                "REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS,
            },
            locale=locale,
        )
