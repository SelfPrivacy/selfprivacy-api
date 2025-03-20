from typing_extensions import Optional
from selfprivacy_api.models.email_password_metadata import EmailPasswordData
from uuid import UUID, uuid4
from datetime import datetime

from selfprivacy_api.repositories.email_password import ACTIVE_EMAIL_PASSWORD_PROVIDER

from passlib.hash import argon2


def _generate_password_hash(password: str) -> str:
    return argon2.hash(password)


def get_email_credentials_metadata(username: str) -> list[EmailPasswordData]:
    return ACTIVE_EMAIL_PASSWORD_PROVIDER.get_all_email_passwords_metadata(
        username=username,
    )


def get_email_credentials_metadata_with_passwords_hashes(
    username: str,
) -> list[EmailPasswordData]:
    return ACTIVE_EMAIL_PASSWORD_PROVIDER.get_all_email_passwords_metadata(
        username=username,
        with_passwords_hashes=True,
    )


def add_email_password(
    username: str,
    password: str,
    display_name: Optional[str] = None,
    with_created_at: Optional[bool] = False,
    with_zero_uuid: Optional[bool] = False,
) -> None:
    add_email_password_hash(
        username=username,
        password_hash=_generate_password_hash(password=password),
        display_name=display_name,
        with_created_at=with_created_at,
        with_zero_uuid=with_zero_uuid,
    )


def add_email_password_hash(
    username: str,
    password_hash: str,
    display_name: Optional[str] = None,
    with_created_at: Optional[bool] = False,
    with_zero_uuid: Optional[bool] = False,
) -> None:
    credential_metadata = EmailPasswordData(
        # UUID(int=0) == '00000000-0000-0000-0000-000000000000'
        uuid=str(UUID(int=0)) if with_zero_uuid else str(uuid4()),
        display_name=display_name if display_name else "Legacy password",
        created_at=datetime.now().isoformat() if with_created_at else None,
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
        if argon2.verify(password, i.hash):
            return True
    return False
