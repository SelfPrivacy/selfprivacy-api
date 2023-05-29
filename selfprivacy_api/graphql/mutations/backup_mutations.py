import datetime
import typing
import strawberry
from strawberry.types import Info

from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.graphql.mutations.mutation_interface import (
    GenericMutationReturn,
    MutationReturnInterface,
)
from selfprivacy_api.graphql.queries.backup import BackupConfiguration
from selfprivacy_api.graphql.queries.backup import Backup
from selfprivacy_api.graphql.queries.providers import BackupProvider

from selfprivacy_api.backup import Backups


@strawberry.input
class InitializeRepositoryInput:
    """Initialize repository input"""

    provider: BackupProvider
    # The following field may become optional for other providers?
    # Backblaze takes bucket id and name
    location_id: str
    location_name: str
    # Key ID and key for Backblaze
    login: str
    password: str


@strawberry.type
class GenericBackupConfigReturn(MutationReturnInterface):
    """Generic backup config return"""

    configuration: typing.Optional[BackupConfiguration]


@strawberry.type
class BackupMutations:
    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def initialize_repository(
        self, repository: InitializeRepositoryInput
    ) -> GenericBackupConfigReturn:
        """Initialize a new repository"""
        provider = Backups.construct_provider(
            kind=repository.provider,
            login=repository.login,
            key=repository.password,
            location=repository.location_name,
            repo_id=repository.location_id,
        )
        Backups.set_provider(provider)
        Backups.init_repo()


@strawberry.mutation(permission_classes=[IsAuthenticated])
def remove_repository(self) -> GenericBackupConfigReturn:
    """Remove repository"""
    Backups.reset()
    return Backup.configuration()
