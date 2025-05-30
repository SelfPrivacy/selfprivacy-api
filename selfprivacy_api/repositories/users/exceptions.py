class UserNotFound(Exception):
    """User not found"""

    @staticmethod
    def get_error_message() -> str:
        return "User not found"


class UserOrGroupNotFound(Exception):
    """User or group not found"""

    @staticmethod
    def get_error_message() -> str:
        return "User or group not found"


class UserIsProtected(Exception):
    """User is protected and cannot be deleted or modified"""

    @staticmethod
    def get_error_message() -> str:
        return "User is protected and cannot be deleted or modified"


class UsernameForbidden(Exception):
    """Username is forbidden"""

    @staticmethod
    def get_error_message() -> str:
        return "Username is forbidden"


class UserAlreadyExists(Exception):
    """User already exists"""

    @staticmethod
    def get_error_message() -> str:
        return "User already exists"


class UsernameNotAlphanumeric(Exception):
    """Username must be alphanumeric and start with a letter"""

    @staticmethod
    def get_error_message() -> str:
        return "Username must be alphanumeric and start with a letter"


class UsernameTooLong(Exception):
    """Username is too long. Must be less than 32 characters"""

    @staticmethod
    def get_error_message() -> str:
        return "Username is too long. Must be less than 32 characters"


class PasswordIsEmpty(Exception):
    """Password cannot be empty"""

    @staticmethod
    def get_error_message() -> str:
        return "Password cannot be empty"


class InvalidConfiguration(Exception):
    """Invalid configuration, userdata is broken"""

    @staticmethod
    def get_error_message() -> str:
        return "Invalid configuration, userdata is broken"


class NoPasswordResetLinkFoundInResponse(Exception):
    """No password reset link was found in the Kanidm response."""

    @staticmethod
    def get_error_message() -> str:
        return "The Kanidm response does not contain a password reset link."


class DisplaynameTooLong(Exception):
    """Display name is too long. Must be less than 16 characters"""

    @staticmethod
    def get_error_message() -> str:
        return "Display name is too long. Must be less than 16 characters"


# from selfprivacy_api.utils.strings import PLEASE_UPDATE_APP_TEXT

# class SelfPrivacyAppIsOutdate(Exception):
#     """
#     SelfPrivacy app is out of date, please update. Some important functions are not working at the moment.
#     """

#     @staticmethod
#     def get_error_message() -> str:
#         return PLEASE_UPDATE_APP_TEXT
