from typing import Optional

import strawberry

from selfprivacy_api.actions.email_passwords import (
    get_email_credentials_metadata as action_get_email_credentials_metadata,
)


@strawberry.type
class EmailPasswordMetadata:
    uuid: str
    display_name: str
    created_at: Optional[str] = None
    expires_at: Optional[str] = None
    last_used: Optional[str] = None


def get_email_credentials_metadata(username: str) -> list[EmailPasswordMetadata]:
    email_credintials_metadata_list = action_get_email_credentials_metadata(
        username=username
    )

    if not email_credintials_metadata_list:
        return []

    return [
        EmailPasswordMetadata(
            uuid=email_credintial_metadata.uuid,
            display_name=email_credintial_metadata.display_name,
            created_at=email_credintial_metadata.created_at,
            expires_at=email_credintial_metadata.expires_at,
            last_used=email_credintial_metadata.last_used,
        )
        for email_credintial_metadata in email_credintials_metadata_list
    ]
