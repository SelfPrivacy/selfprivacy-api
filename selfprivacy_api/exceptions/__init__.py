import gettext
import logging
from textwrap import dedent

from selfprivacy_api.exceptions.abstract_exception import AbstractException
from selfprivacy_api.utils.localization import (
    DEFAULT_LOCALE,
    TranslateSystemMessage as t,
)

logger = logging.getLogger(__name__)

_ = gettext.gettext

PLEASE_UPDATE_APP_TEXT = _(
    "Your SelfPrivacy app is out of date, please update it to use new features."
)

REPORT_IT_TO_SUPPORT_CHATS = _(
    dedent(
        """
        Please report it to our support chats:
        https://matrix.to/#/#chat:selfprivacy.org
        https://t.me/selfprivacy_chat
        """
    )
)

KANIDM_DESCRIPTION = _(
    "Kanidm is the identity and authentication service that manages users and access to system services."
)

KANIDM_PROBLEMS = _("There may have been a Kanidm update that broke compatibility.")

KANIDM_DEBUG_HELP = _(
    dedent(
        """
        Console commands to debug:
            "systemctl status kanidm.service"
            "journalctl -u kanidm.service -f"
        """
    )
)


class ApiUsingWrongUserRepository(AbstractException):
    """
    API is using a too old or unfinished user repository. Are you debugging?
    """

    code = 500

    def __init__(self):
        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_("API is using a too old or unfinished user repository"),
            locale=locale,
        )
