"""Known system update channels"""

import gettext
import typing
from dataclasses import dataclass

_ = gettext.gettext


@dataclass(frozen=True)
class UpdateChannelDefinition:
    """Untranslated definition of an update channel"""

    id: str
    update_url: str
    name: str
    description: str


UPDATE_CHANNELS: typing.Tuple[UpdateChannelDefinition, ...] = (
    UpdateChannelDefinition(
        id="stable",
        update_url="git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes",
        name=_("Stable channel"),
        description=_("Latest tested release of SelfPrivacy system"),
    ),
)


def find_update_channel(update_url: str) -> typing.Optional[UpdateChannelDefinition]:
    """Find a channel matching the given update URL"""
    for definition in UPDATE_CHANNELS:
        if definition.update_url == update_url:
            return definition

    return None


def find_update_channel_by_id(
    channel_id: str,
) -> typing.Optional[UpdateChannelDefinition]:
    """Find a channel by its id"""
    for definition in UPDATE_CHANNELS:
        if definition.id == channel_id:
            return definition

    return None
