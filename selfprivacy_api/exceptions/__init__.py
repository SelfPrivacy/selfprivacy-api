import gettext

from selfprivacy_api.exceptions.abstract_exception import AbstractException
from selfprivacy_api.utils.localization import (
    DEFAULT_LOCALE,
    TranslateSystemMessage as t,
)

_ = gettext.gettext

PLEASE_UPDATE_APP_TEXT = _(
    "Your SelfPrivacy app is out of date, please update it to use new features."
)

REPORT_IT_TO_SUPPORT_CHATS = _(
    "Please report it to our support chats:\n"
    "#chat:selfprivacy.org on Matrix or @selprivacy_chat on Telegram."
)


class ApiUsingWrongUserRepository(AbstractException):
    """
    The API is using wrong user repository. Are you debugging?
    """

    code = 500

    def __init__(self, log: bool = True):
        super().__init__(log=log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_("The API is using the wrong user repository."),
            locale=locale,
        )
