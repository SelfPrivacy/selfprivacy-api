<<<<<<< HEAD
import secrets
import base64
import unicodedata

from passlib.hash import argon2, sha512_crypt

from selfprivacy_api.repositories.email_password import ACTIVE_EMAIL_PASSWORD_PROVIDER
from selfprivacy_api.models.email_password_metadata import EmailPasswordData


def generate_urlsave_password() -> str:
    random_bytes = secrets.token_bytes(32)
    return base64.urlsafe_b64encode(random_bytes).decode("utf-8")


def generate_password_hash(password: str) -> str:
    return argon2.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    password = unicodedata.normalize("NFKC", password)

    if "$argon2" in password_hash:
        return argon2.verify(password, password_hash)
    else:
        return sha512_crypt.verify(password, password_hash)
=======
from datetime import datetime, timezone
from typing import Optional
import logging

from selfprivacy_api.repositories.email_password import ACTIVE_EMAIL_PASSWORD_PROVIDER
from selfprivacy_api.models.email_password_metadata import EmailPasswordData
from selfprivacy_api.utils.argon2 import (
    verify_password,
    generate_urlsave_password,
)
from selfprivacy_api.actions.email_passwords import add_email_password

logger = logging.getLogger(__name__)
>>>>>>> d5eaf399d26f7350239b524ac291a6b5711b6b72


def get_email_credentials_metadata_with_passwords_hashes(
    username: str,
) -> list[EmailPasswordData]:
    return ACTIVE_EMAIL_PASSWORD_PROVIDER.get_all_email_passwords_metadata(
        username=username,
        with_passwords_hashes=True,
    )


<<<<<<< HEAD
=======
def is_expired(expires_at: Optional[datetime]) -> bool:
    return expires_at is not None and expires_at < datetime.now(timezone.utc)


>>>>>>> d5eaf399d26f7350239b524ac291a6b5711b6b72
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
<<<<<<< HEAD
        if verify_password(password=password, password_hash=str(i.hash)):
            return True
    return False
=======
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
    password = generate_urlsave_password()
    add_email_password(
        username=username,
        password=password,
        display_name=display_name,
        expires_at=expires_at,
    )
    return password
>>>>>>> d5eaf399d26f7350239b524ac291a6b5711b6b72
