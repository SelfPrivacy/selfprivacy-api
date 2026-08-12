"""Common system-related GraphQL types"""

import strawberry

from selfprivacy_api.update_channels import UpdateChannelDefinition
from selfprivacy_api.utils.localization import TranslateSystemMessage as t


@strawberry.type
class UpdateChannel:
    """Information about update channel"""

    id: str
    update_url: str
    name: str
    description: str


def channel_to_graphql(
    definition: UpdateChannelDefinition, locale: str
) -> UpdateChannel:
    """Convert a channel definition to a GraphQL type with translated strings"""
    return UpdateChannel(
        id=definition.id,
        update_url=definition.update_url,
        name=t.translate(text=definition.name, locale=locale),
        description=t.translate(text=definition.description, locale=locale),
    )
