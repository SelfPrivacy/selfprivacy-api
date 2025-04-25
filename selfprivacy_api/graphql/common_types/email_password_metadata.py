from typing import Optional
from datetime import datetime

import strawberry

from selfprivacy_api.actions.email_passwords import (
    get_email_credentials_metadata as action_get_email_credentials_metadata,
)


@strawberry.type
class EmailPasswordMetadata:
    uuid: str
    display_name: str
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None


def get_email_credentials_metadata(username: str) -> list[EmailPasswordMetadata]:
    email_credentials_metadata_list = action_get_email_credentials_metadata(
        username=username
    )

    if not email_credentials_metadata_list:
        return []

    return [
        EmailPasswordMetadata(
            uuid=email_credential_metadata.uuid,
            display_name=email_credential_metadata.display_name,
            created_at=email_credential_metadata.created_at,
            expires_at=email_credential_metadata.expires_at,
            last_used=email_credential_metadata.last_used,
        )
        for email_credential_metadata in email_credentials_metadata_list
    ]
