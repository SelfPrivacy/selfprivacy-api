class UserNotFound(Exception):
    """Attemted to get a user that does not exist"""


class UserIsProtected(Exception):
    """Attemted to delete a user that is protected"""


class UsernameForbidden(Exception):
    """Attemted to create a user with a forbidden username"""


class UserAlreadyExists(Exception):
    """Attemted to create a user that already exists"""


class UsernameNotAlphanumeric(Exception):
    """Attemted to create a user with a non-alphanumeric username"""


class UsernameTooLong(Exception):
    """Attemted to create a user with a too long username. Username must be less than 32 characters"""


class PasswordIsEmpty(Exception):
    """Attemted to create a user with an empty password"""


class InvalidConfiguration(Exception):
    """The userdata is broken"""


class SelfPrivacyAppIsOutdate(Exception):
    """SelfPrivacy app is out of date, please update. Some important functions are not working at the moment."""
