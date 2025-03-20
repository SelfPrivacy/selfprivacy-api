from typing_extensions import Optional
from selfprivacy_api.models.email_password_metadata import EmailPasswordData
from uuid import UUID, uuid4
from datetime import datetime, timezone

from selfprivacy_api.models.tokens.time import ensure_timezone
from selfprivacy_api.repositories.email_password import ACTIVE_EMAIL_PASSWORD_PROVIDER

from passlib.hash import argon2

from selfprivacy_api.utils.argon2 import generate_password_hash


def get_email_credentials_metadata(username: str) -> list[EmailPasswordData]:
    return ACTIVE_EMAIL_PASSWORD_PROVIDER.get_all_email_passwords_metadata(
        username=username,
    )


def add_email_password(
    username: str,
    password: str,
    display_name: Optional[str] = None,
    with_created_at: Optional[bool] = False,
    with_zero_uuid: Optional[bool] = False,
    expires_at: Optional[datetime] = None,
) -> None:
    add_email_password_hash(
        username=username,
        password_hash=generate_password_hash(password),
        display_name=display_name,
        with_created_at=with_created_at,
        with_zero_uuid=with_zero_uuid,
        expires_at=expires_at,
    )


def add_email_password_hash(
    username: str,
    password_hash: str,
    display_name: Optional[str] = None,
    with_created_at: Optional[bool] = False,
    with_zero_uuid: Optional[bool] = False,
    expires_at: Optional[datetime] = None,
) -> None:
    credential_metadata = EmailPasswordData(
        # UUID(int=0) == '00000000-0000-0000-0000-000000000000'
        uuid=str(UUID(int=0)) if with_zero_uuid else str(uuid4()),
        display_name=display_name if display_name else "Legacy password",
        created_at=datetime.now(timezone.utc) if with_created_at else None,
        expires_at=ensure_timezone(expires_at) if expires_at else None,
    )

    ACTIVE_EMAIL_PASSWORD_PROVIDER.add_email_password_hash(
        username=username,
        password_hash=password_hash,
        credential_metadata=credential_metadata,
    )


def delete_email_password_hash(username: str, uuid: str) -> None:
    ACTIVE_EMAIL_PASSWORD_PROVIDER.delete_email_password_hash(
        username=username, uuid=uuid
    )


def update_legacy_email_password_hash(
    username: str, password: str, with_created_at: Optional[bool] = False
):
    # UUID(int=0) == '00000000-0000-0000-0000-000000000000'
    delete_email_password_hash(username=username, uuid=str(UUID(int=0)))
    add_email_password(
        username=username,
        password=password,
        with_created_at=True,
    )


def delete_all_email_passwords_hashes(username: str):
    ACTIVE_EMAIL_PASSWORD_PROVIDER.delete_all_email_passwords_hashes(username)
