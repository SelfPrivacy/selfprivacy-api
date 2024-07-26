"""
New device key used to obtain access token.
"""

from datetime import datetime, timedelta, timezone
import secrets
from pydantic import BaseModel
from mnemonic import Mnemonic

from selfprivacy_api.models.tokens.time import is_past


class NewDeviceKey(BaseModel):
    """
    Recovery key used to obtain access token.

    Recovery key has a key string, date of creation, date of expiration.
    """

    key: str
    created_at: datetime
    expires_at: datetime

    def is_valid(self) -> bool:
        """
        Check if key is valid.
        """
        if is_past(self.expires_at):
            return False
        return True

    def as_mnemonic(self) -> str:
        """
        Get the key as a mnemonic.
        """
        return Mnemonic(language="english").to_mnemonic(bytes.fromhex(self.key))

    @staticmethod
    def generate() -> "NewDeviceKey":
        """
        Factory to generate a random token.
        """
        creation_date = datetime.now(timezone.utc)
        key = secrets.token_bytes(16).hex()
        return NewDeviceKey(
            key=key,
            created_at=creation_date,
            expires_at=creation_date + timedelta(minutes=10),
        )
