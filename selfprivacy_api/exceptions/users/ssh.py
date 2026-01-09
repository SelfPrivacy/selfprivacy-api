import gettext
import logging

from selfprivacy_api.exceptions.abstract_exception import AbstractException
from selfprivacy_api.utils.localization import (
    DEFAULT_LOCALE,
    TranslateSystemMessage as t,
)

_ = gettext.gettext

logger = logging.getLogger(__name__)

# https://www.openssh.org/specs.html
VALID_SSH_KEY_TYPES = [
    "ssh-ed25519",
    "ecdsa-sha2-nistp256",
    "ecdsa-sha2-nistp384",
    "ecdsa-sha2-nistp521",
    "sk-ssh-ed25519@openssh.com",
    # OpenSSH supports only P-256 for sk-ecdsa- keys.
    "sk-ecdsa-sha2-nistp256@openssh.com",
]


class KeyNotFound(AbstractException):
    """Key not found"""

    code = 404

    def __init__(self):
        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(text=_("Key not found"), locale=locale)


class KeyAlreadyExists(AbstractException):
    """Key already exists"""

    code = 409

    def __init__(self):
        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(text=_("Key already exists"), locale=locale)


class InvalidPublicKey(AbstractException):
    """Invalid public key"""

    def __init__(self):
        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_("Invalid key type. Supported key types: "),
            locale=locale,
        ) + ", ".join(VALID_SSH_KEY_TYPES)
