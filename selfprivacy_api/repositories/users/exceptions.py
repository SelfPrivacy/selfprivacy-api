import gettext

from selfprivacy_api.utils.localization import TranslateSystemMessage as t

_ = gettext.gettext


class UserNotFound(Exception):
    """User not found"""

    @staticmethod
    def get_error_message(locale: str) -> str:
        return t.translate(text=_("User not found"), locale="ru")


class UserOrGroupNotFound(Exception):
    """User or group not found"""

    @staticmethod
    def get_error_message(locale: str) -> str:
        return t.translate(text=_("User or group not found"), locale=locale)


class UserIsProtected(Exception):
    """User is protected and cannot be deleted or modified"""

    @staticmethod
    def get_error_message(locale: str) -> str:
        return t.translate(
            text=_("User is protected and cannot be deleted or modified"), locale=locale
        )


class UsernameForbidden(Exception):
    """Username is forbidden"""

    @staticmethod
    def get_error_message(locale: str) -> str:
        return t.translate(text=_("Username is forbidden"), locale=locale)


class UserAlreadyExists(Exception):
    """User already exists"""

    @staticmethod
    def get_error_message(locale: str) -> str:
        return t.translate(text=_("User already exists"), locale=locale)


class UsernameNotAlphanumeric(Exception):
    """Username must be alphanumeric and start with a letter"""

    @staticmethod
    def get_error_message(locale: str) -> str:
        return t.translate(
            text=_("Username must be alphanumeric and start with a letter"),
            locale=locale,
        )


class UsernameTooLong(Exception):
    """Username is too long. Must be less than 32 characters"""

    @staticmethod
    def get_error_message(locale: str) -> str:
        return t.translate(
            text=_("Username is too long. Must be less than 32 characters"),
            locale=locale,
        )


class PasswordIsEmpty(Exception):
    """Password cannot be empty"""

    @staticmethod
    def get_error_message(locale: str) -> str:
        return t.translate(text=_("Password cannot be empty"), locale=locale)


class InvalidConfiguration(Exception):
    """Invalid configuration, userdata is broken"""

    @staticmethod
    def get_error_message(locale: str) -> str:
        return t.translate(
            text=_("Invalid configuration, userdata is broken"), locale=locale
        )


class NoPasswordResetLinkFoundInResponse(Exception):
    """No password reset link was found in the Kanidm response."""

    @staticmethod
    def get_error_message(locale: str) -> str:
        return t.translate(
            text=_("The Kanidm response does not contain a password reset link."),
            locale=locale,
        )


class DisplaynameTooLong(Exception):
    """Display name is too long. Must be less than 16 characters"""

    @staticmethod
    def get_error_message(locale: str) -> str:
        return t.translate(
            text=_("Display name is too long. Must be less than 16 characters"),
            locale=locale,
        )
