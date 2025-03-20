import secrets
import base64
import unicodedata

from passlib.hash import argon2, sha512_crypt


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
