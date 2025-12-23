import gettext
import logging
from textwrap import dedent
from typing import List, Literal

from selfprivacy_api.utils.localization import (
    DEFAULT_LOCALE,
    TranslateSystemMessage as t,
)

_ = gettext.gettext

logger = logging.getLogger(__name__)


class UserNotFound(Exception):
    """User not found"""

    def __init__(self):
        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(text=_("User not found"), locale=locale)


class UserOrGroupNotFound(Exception):
    """User or group not found"""

    code = 404

    def __init__(self):
        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_(
                dedent(
                    """
                    User or group not found.
                    Kanidm is a user management program that controls users and permission groups.
                    If Kanidm cannot find either a user or a group, it returns the same error message for both cases,
                    which makes it difficult to distinguish between them.
                    """
                )
            ),
            locale=locale,
        )


class UserIsProtected(Exception):
    """User is protected and cannot be deleted or modified"""

    code = 400

    def __init__(self, account_type: Literal["root", "primary"]):
        if account_type not in ("root", "primary"):
            raise ValueError("Invalid account_type")
        self.account_type = account_type

        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_(
                dedent(
                    """
                    User is protected and cannot be deleted or modified.
                    Reason: %(root_or_primary)s account.
                    """
                )
                % {"root_or_primary": self.account_type}
            ),
            locale=locale,
        )


class UsernameForbidden(Exception):
    """Username is forbidden"""

    code = 409

    def __init__(
        self,
        forbudden_usernames: List[str],
        forbudden_prefixes: List[str],
    ):
        self.forbudden_usernames = forbudden_usernames
        self.forbudden_prefixes = forbudden_prefixes

        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_(
                dedent(
                    """
                    Username is in forbidden list or have forbidden prefix.
                    List of forbudden usernames: %(forbudden_usernames)s.
                    List of forbudden prefixes: %(forbudden_prefixes)s.
                    """
                )
                % {
                    "forbudden_usernames": self.forbudden_usernames,
                    "forbudden_prefixes": self.forbudden_prefixes,
                }
            ),
            locale=locale,
        )


class UserAlreadyExists(Exception):
    """User already exists"""

    code = 409

    def __init__(self):
        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(text=_("User already exists"), locale=locale)


class UsernameNotAlphanumeric(Exception):
    """Username must be alphanumeric and start with a letter"""

    code = 400

    def __init__(self, regex_pattern: str):
        self.regex_pattern = regex_pattern

        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_(
                dedent(
                    """
                    Username must be alphanumeric and start with a letter.
                    Used regex pattern: %(regex_pattern)s.
                    """
                )
            )
            % {"regex_pattern": self.regex_pattern},
            locale=locale,
        )


class UsernameTooLong(Exception):
    """Username is too long. Must be less than 32 characters"""

    code = 400

    def __init__(self):
        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_("Username is too long. Must be less than 32 characters."),
            locale=locale,
        )


class PasswordIsEmpty(Exception):
    """Password cannot be empty"""

    code = 400

    def __init__(self):
        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(text=_("Password cannot be empty."), locale=locale)


class DisplaynameTooLong(Exception):
    """Display name is too long. Must be less than 16 characters"""

    code = 400

    def __init__(self):
        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_("Display name is too long. Must be less than 16 characters."),
            locale=locale,
        )


USERS_REPOSITORY_EXCEPTIONS = (
    DisplaynameTooLong,
    PasswordIsEmpty,
    UserAlreadyExists,
    UserIsProtected,
    UsernameForbidden,
    UsernameNotAlphanumeric,
    UsernameTooLong,
    UserNotFound,
    UserOrGroupNotFound,
)
