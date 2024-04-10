from typing import Type

from selfprivacy_api.graphql.queries.providers import (
    BackupProvider as BackupProviderEnum,
)
from selfprivacy_api.backup.providers.provider import AbstractBackupProvider

from selfprivacy_api.backup.providers.backblaze import Backblaze
from selfprivacy_api.backup.providers.memory import InMemoryBackup
from selfprivacy_api.backup.providers.local_file import LocalFileBackup
from selfprivacy_api.backup.providers.none import NoBackups

PROVIDER_MAPPING: dict[BackupProviderEnum, Type[AbstractBackupProvider]] = {
    BackupProviderEnum.BACKBLAZE: Backblaze,
    BackupProviderEnum.MEMORY: InMemoryBackup,
    BackupProviderEnum.FILE: LocalFileBackup,
    BackupProviderEnum.NONE: NoBackups,
}


def get_provider(
    provider_type: BackupProviderEnum,
) -> Type[AbstractBackupProvider]:
    if provider_type not in PROVIDER_MAPPING.keys():
        raise LookupError("could not look up provider", provider_type)
    return PROVIDER_MAPPING[provider_type]


def get_kind(provider: AbstractBackupProvider) -> str:
    """Get the kind of the provider in the form of a string"""
    return provider.name.value
