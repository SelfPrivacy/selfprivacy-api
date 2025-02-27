from selfprivacy_api.models.email_password_metadata import EmailPasswordMetadata
from uuid import uuid4

from selfprivacy_api.repositories.email_password import ACTIVE_EMAIL_PASSWORD_PROVIDER


def get_email_credentials_metadata(username: str) -> list[EmailPasswordMetadata]:
    return ACTIVE_EMAIL_PASSWORD_PROVIDER.get_all_email_passwords_metadata(
        username=username,
    )


def add_email_password(username: str, password_hash: str) -> None:
    credential_metadata = EmailPasswordMetadata(
        uuid=str(uuid4()),
        display_name="Legacy password",
    )

    ACTIVE_EMAIL_PASSWORD_PROVIDER.add_new_email_password(
        username=username,
        password_hash=password_hash,
        credential_metadata=credential_metadata,
    )


def delete_email_password(username: str, uuid: str) -> None:
    ACTIVE_EMAIL_PASSWORD_PROVIDER.delete_email_password(username=username, uuid=uuid)
