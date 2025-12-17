import gettext
from textwrap import dedent

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
