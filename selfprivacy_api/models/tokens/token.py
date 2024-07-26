"""
Model of the access token.

Access token has a token string, device name and date of creation.
"""

from datetime import datetime
import secrets
from pydantic import BaseModel


class Token(BaseModel):
    """
    Model of the access token.

    Access token has a token string, device name and date of creation.
    """

    token: str
    device_name: str
    created_at: datetime

    @staticmethod
    def generate(device_name: str) -> "Token":
        """
        Factory to generate a random token.
        """
        creation_date = datetime.now()
        token = secrets.token_urlsafe(32)
        return Token(
            token=token,
            device_name=device_name,
            created_at=creation_date,
        )
