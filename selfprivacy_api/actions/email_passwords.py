from typing_extensions import Optional
from selfprivacy_api.models.email_password_metadata import EmailPasswordMetadata
from uuid import uuid4
from datetime import datetime

from selfprivacy_api.repositories.email_password import ACTIVE_EMAIL_PASSWORD_PROVIDER


def get_email_credentials_metadata(username: str) -> list[EmailPasswordMetadata]:
    return ACTIVE_EMAIL_PASSWORD_PROVIDER.get_all_email_passwords_metadata(
        username=username,
    )


def add_email_password(
    username: str,
    password_hash: str,
    display_name: Optional[str] = None,
    with_created_at: Optional[bool] = False,
    with_zero_uuid: Optional[bool] = False,
) -> None:
    zero_uuid = "00000000-0000-0000-0000-000000000000"

    credential_metadata = EmailPasswordMetadata(
        uuid=zero_uuid if with_zero_uuid else str(uuid4()),
        display_name=display_name if display_name else "Legacy password",
        created_at=datetime.now().isoformat() if with_created_at else None,
    )

    ACTIVE_EMAIL_PASSWORD_PROVIDER.add_new_email_password(
        username=username,
        password_hash=password_hash,
        credential_metadata=credential_metadata,
    )


def delete_email_password(username: str, uuid: str) -> None:
    ACTIVE_EMAIL_PASSWORD_PROVIDER.delete_email_password(username=username, uuid=uuid)


def update_legecy_email_password(
    username: str, password_hash: str, with_created_at: Optional[bool] = False
):
    zero_uuid = "00000000-0000-0000-0000-000000000000"

    delete_email_password(username=username, uuid=zero_uuid)
    add_email_password(
        username=username, password_hash=password_hash, with_created_at=True
    )


def delete_all_email_passwords(username: str):
    email_passwords = get_email_credentials_metadata(username=username)

    for email_password in email_passwords:
        delete_email_password(username=username, uuid=email_password.uuid)
