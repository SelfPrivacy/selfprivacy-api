import gettext

from selfprivacy_api.exceptions.abstract_exception import AbstractException
from selfprivacy_api.exceptions.kanidm import KANIDM_DESCRIPTION
from selfprivacy_api.utils.localization import (
    DEFAULT_LOCALE,
    TranslateSystemMessage as t,
)

_ = gettext.gettext


class UserNotFound(AbstractException):
    """User not found"""

    code = 404

    def __init__(self, log: bool = True):
        super().__init__(log=log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(text=_("User not found"), locale=locale)


class UserOrGroupNotFound(AbstractException):
    """User or group not found"""

    code = 404

    def __init__(self, log: bool = True):
        super().__init__(log=log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_(
                "User or group not found.\n"
                "Kanidm uses the same error for missing users and groups."
                "%(KANIDM_DESCRIPTION)s\n"
            ),
            locale=locale,
        ) % {"KANIDM_DESCRIPTION": KANIDM_DESCRIPTION}


class RootUserIsProtected(AbstractException):
    """Root user is protected and cannot be deleted or modified"""

    def __init__(self, log: bool = True):
        super().__init__(log=log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_("Root user cannot be deleted or modified."),
            locale=locale,
        )


class UsernameForbidden(AbstractException):
    """Username is reserved"""

    code = 409

    def __init__(
        self,
        forbidden_prefix: str = "",
        log: bool = True,
    ):
        self.forbidden_prefix = forbidden_prefix

        super().__init__(log=log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        if self.forbidden_prefix:
            return t.translate(
                text=_(
                    "Username is in reserved list or have reserved prefix.\n"
                    "Reserved prefix: %(forbidden_prefix)s."
                )
                % {
                    "forbidden_prefix": self.forbidden_prefix,
                },
                locale=locale,
            )
        return t.translate(
            text=_("Username is in reserved list or have reserved prefix."),
            locale=locale,
        )


class UserAlreadyExists(AbstractException):
    """User already exists"""

    code = 409

    def __init__(self, log: bool = True):
        super().__init__(log=log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(text=_("User already exists"), locale=locale)


class UsernameNotAlphanumeric(AbstractException):
    """Username must be alphanumeric and start with a letter"""

    def __init__(self, log: bool = True):
        super().__init__(log=log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_("Username must be alphanumeric and start with a letter.\n"),
            locale=locale,
        )


class UsernameTooLong(AbstractException):
    """Username is too long. Must be less than 32 characters"""

    def __init__(self, log: bool = True):
        super().__init__(log=log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_("Username is too long. Must be less than 32 characters."),
            locale=locale,
        )


class PasswordIsEmpty(AbstractException):
    """Password cannot be empty"""

    def __init__(self, log: bool = True):
        super().__init__(log=log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE, log: bool = True) -> str:
        return t.translate(text=_("Password cannot be empty."), locale=locale)


class DisplaynameTooLong(AbstractException):
    """Display name is too long. Must be less than 16 characters"""

    def __init__(self, log: bool = True):
        super().__init__(log=log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_("Display name is too long. Must be less than 256 characters."),
            locale=locale,
        )
