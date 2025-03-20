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
    return argon2.hash(unicodedata.normalize("NFKC", password))


def verify_password(password: str, password_hash: str) -> bool:
    password = unicodedata.normalize("NFKC", password)

    if "$argon2" in password_hash:
        return argon2.verify(password, password_hash)
    else:
        return sha512_crypt.verify(password, password_hash)


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
