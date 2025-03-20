from datetime import datetime
import secrets
import base64
from typing import Optional
import unicodedata

from passlib.hash import argon2, sha512_crypt

from selfprivacy_api.repositories.email_password import ACTIVE_EMAIL_PASSWORD_PROVIDER
from selfprivacy_api.models.email_password_metadata import EmailPasswordData
from selfprivacy_api.utils.argon2 import (
    verify_password,
    generate_urlsave_password,
    generate_password_hash,
)
from selfprivacy_api.actions.email_passwords import add_email_password


def get_email_credentials_metadata_with_passwords_hashes(
    username: str,
) -> list[EmailPasswordData]:
    return ACTIVE_EMAIL_PASSWORD_PROVIDER.get_all_email_passwords_metadata(
        username=username,
        with_passwords_hashes=True,
    )


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
        if i.hash is None:
            continue
        if verify_password(password=password, password_hash=str(i.hash)):
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
