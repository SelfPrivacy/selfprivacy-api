"""
New device key used to obtain access token.
"""
from datetime import datetime, timedelta
import secrets
from pydantic import BaseModel
from mnemonic import Mnemonic


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
        Check if the recovery key is valid.
        """
        if self.expires_at < datetime.now():
            return False
        return True

    def as_mnemonic(self) -> str:
        """
        Get the recovery key as a mnemonic.
        """
        return Mnemonic(language="english").to_mnemonic(bytes.fromhex(self.key))

    @staticmethod
    def generate() -> "NewDeviceKey":
        """
        Factory to generate a random token.
        """
        creation_date = datetime.now()
        key = secrets.token_bytes(16).hex()
        return NewDeviceKey(
            key=key,
            created_at=creation_date,
            expires_at=datetime.now() + timedelta(minutes=10),
        )
