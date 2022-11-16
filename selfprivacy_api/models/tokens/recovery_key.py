"""
Recovery key used to obtain access token.

Recovery key has a token string, date of creation, optional date of expiration and optional count of uses left.
"""
from datetime import datetime
import secrets
from typing import Optional
from pydantic import BaseModel
from mnemonic import Mnemonic


class RecoveryKey(BaseModel):
    """
    Recovery key used to obtain access token.

    Recovery key has a key string, date of creation, optional date of expiration and optional count of uses left.
    """

    key: str
    created_at: datetime
    expires_at: Optional[datetime]
    uses_left: Optional[int]

    def is_valid(self) -> bool:
        """
        Check if the recovery key is valid.
        """
        if self.expires_at is not None and self.expires_at < datetime.now():
            return False
        if self.uses_left is not None and self.uses_left <= 0:
            return False
        return True

    def as_mnemonic(self) -> str:
        """
        Get the recovery key as a mnemonic.
        """
        return Mnemonic(language="english").to_mnemonic(bytes.fromhex(self.key))

    @staticmethod
    def generate(
        expiration: Optional[datetime],
        uses_left: Optional[int],
    ) -> "RecoveryKey":
        """
        Factory to generate a random token.
        """
        creation_date = datetime.now()
        key = secrets.token_bytes(24).hex()
        return RecoveryKey(
            key=key,
            created_at=creation_date,
            expires_at=expiration,
            uses_left=uses_left,
        )
