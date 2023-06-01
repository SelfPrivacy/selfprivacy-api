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
from selfprivacy_api.services import get_all_services, get_service_by_id
from selfprivacy_api.backup.tasks import start_backup, restore_snapshot


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


class GenericJobMutationReturn:
    pass


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

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def start_backup(
        self, service_id: typing.Optional[str] = None
    ) -> GenericJobMutationReturn:
        """Start backup. If service not provided, backup all services"""
        if service_id is None:
            for service in get_all_services():
                start_backup(service)
        else:
            service = get_service_by_id(service_id)
            if service is None:
                raise ValueError(f"nonexistent service: {service_id}")
            start_backup(service)

        return GenericJobMutationReturn()

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def restore_backup(self, snapshot_id: str) -> GenericJobMutationReturn:
        """Restore backup"""
        snap = Backups.get_snapshot_by_id(snapshot_id)
        if snap in None:
            raise ValueError(f"No such snapshot: {snapshot_id}")
        restore_snapshot(snap)

        return GenericJobMutationReturn()

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def force_snapshots_reload(self) -> GenericMutationReturn:
        """Force snapshots reload"""
        Backups.force_snapshot_reload()
        return GenericMutationReturn()
