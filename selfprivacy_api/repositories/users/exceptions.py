class UserNotFound(Exception):
    """Attempted to get a user that does not exist"""

    @staticmethod
    def get_error_message() -> str:
        return "User not found"


class UserIsProtected(Exception):
    """Attempted to delete a user that is protected"""

    @staticmethod
    def get_error_message() -> str:
        return "User is protected and cannot be deleted"


class UsernameForbidden(Exception):
    """Attempted to create a user with a forbidden username"""

    @staticmethod
    def get_error_message() -> str:
        return "Username is forbidden"


class UserAlreadyExists(Exception):
    """Attempted to create a user that already exists"""

    @staticmethod
    def get_error_message() -> str:
        return "User already exists"


class UsernameNotAlphanumeric(Exception):
    """Attempted to create a user with a non-alphanumeric username"""

    @staticmethod
    def get_error_message() -> str:
        return "Username not alphanumeric"


class UsernameTooLong(Exception):
    """
    Attempted to create a user with a too long username. Username must be less than 32 characters
    """

    @staticmethod
    def get_error_message() -> str:
        return "Username is too long. Must be less than 32 characters"


class PasswordIsEmpty(Exception):
    """Attempted to create a user with an empty password"""

    @staticmethod
    def get_error_message() -> str:
        return "Password cannot be empty"


class InvalidConfiguration(Exception):
    """The userdata is broken"""

    @staticmethod
    def get_error_message() -> str:
        return "Invalid configuration, userdata is broken"


class SelfPrivacyAppIsOutdate(Exception):
    """
    SelfPrivacy app is out of date, please update. Some important functions are not working at the moment.
    """

    @staticmethod
    def get_error_message() -> str:
        return "SelfPrivacy app is out of date, please update"
