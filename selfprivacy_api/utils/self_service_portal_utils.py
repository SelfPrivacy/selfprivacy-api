import base64
from datetime import datetime, timezone
from io import BytesIO
from typing import Optional
import logging

import qrcode
from qrcode.image.pure import PyPNGImage
import qrcode.image.pure
import diceware

from selfprivacy_api.repositories.email_password import ACTIVE_EMAIL_PASSWORD_PROVIDER
from selfprivacy_api.models.email_password_metadata import EmailPasswordData
from selfprivacy_api.utils.argon2 import (
    verify_password,
    generate_urlsave_password,
)
from selfprivacy_api.actions.email_passwords import add_email_password

logger = logging.getLogger(__name__)


def get_email_credentials_metadata_with_passwords_hashes(
    username: str,
) -> list[EmailPasswordData]:
    return ACTIVE_EMAIL_PASSWORD_PROVIDER.get_all_email_passwords_metadata(
        username=username,
        with_passwords_hashes=True,
    )


def is_expired(expires_at: Optional[datetime]) -> bool:
    return expires_at is not None and expires_at < datetime.now(timezone.utc)


def validate_email_password(username: str, password: str) -> bool:
    email_passwords_data = (
        ACTIVE_EMAIL_PASSWORD_PROVIDER.get_all_email_passwords_metadata(
            username=username,
            with_passwords_hashes=True,
        )
    )
    if not email_passwords_data:
        return False

    for i in email_passwords_data:
        if i.password is None:
            continue
        if is_expired(i.expires_at):
            continue
        if verify_password(password=password, password_hash=str(i.password)):
            try:
                ACTIVE_EMAIL_PASSWORD_PROVIDER.update_email_password_hash_last_used(
                    username=username,
                    uuid=i.uuid,
                )
            except Exception as e:
                logger.error(f"Failed to update email password hash last_used: {e}")
            return True
    return False


def generate_new_email_password(
    username: str, display_name: str, expires_at: Optional[datetime]
) -> str:
    password = diceware.get_passphrase(
        options=diceware.handle_options(args=["-d", "-", "--no-caps"])
    )
    add_email_password(
        username=username,
        password=password,
        display_name=display_name,
        expires_at=expires_at,
    )
    return password


def generate_qr_code(data: str) -> str:
    qr: PyPNGImage = qrcode.make(data, image_factory=qrcode.image.pure.PyPNGImage)
    buffered = BytesIO()
    qr.save(buffered)
    return base64.b64encode(buffered.getvalue()).decode("utf-8", "replace")
