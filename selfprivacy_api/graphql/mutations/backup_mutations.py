import datetime
import typing
import strawberry
from strawberry.types import Info

from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.graphql.mutations.mutation_interface import (
    GenericMutationReturn,
    GenericJobButationReturn,
    MutationReturnInterface,
)
from selfprivacy_api.graphql.queries.backup import BackupConfiguration
from selfprivacy_api.graphql.queries.backup import Backup
from selfprivacy_api.graphql.queries.providers import BackupProvider
from selfprivacy_api.graphql.common_types.jobs import job_to_api_job

from selfprivacy_api.backup import Backups
from selfprivacy_api.services import get_all_services, get_service_by_id
from selfprivacy_api.backup.tasks import start_backup, restore_snapshot
from selfprivacy_api.backup.jobs import add_backup_job, add_restore_job


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
        Backups.set_provider(
            kind=repository.provider.value,
            login=repository.login,
            key=repository.password,
            location=repository.location_name,
            repo_id=repository.location_id,
        )
        Backups.init_repo()
        return GenericBackupConfigReturn(
            success=True, message="", code="200", configuration=Backup().configuration()
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def remove_repository(self) -> GenericBackupConfigReturn:
        """Remove repository"""
        Backups.reset()
        return GenericBackupConfigReturn(
            success=True, message="", code="200", configuration=Backup().configuration()
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def set_autobackup_period(
        self, period: typing.Optional[int] = None
    ) -> GenericBackupConfigReturn:
        """Set autobackup period. None is to disable autobackup"""
        Backups.set_autobackup_period_minutes(period)
        return GenericBackupConfigReturn(
            success=True, message="", code="200", configuration=Backup().configuration()
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def start_backup(self, service_id: str) -> GenericJobButationReturn:
        """Start backup"""

        service = get_service_by_id(service_id)
        if service is None:
            return GenericJobButationReturn(
                success=False,
                code=300,
                message=f"nonexistent service: {service_id}",
                job=None,
            )

        job = add_backup_job(service)
        start_backup(service)
        job = job_to_api_job(job)

        return GenericJobButationReturn(
            success=True,
            code=200,
            message="Backup job queued",
            job=job,
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def restore_backup(self, snapshot_id: str) -> GenericJobButationReturn:
        """Restore backup"""
        snap = Backups.get_snapshot_by_id(snapshot_id)
        service = get_service_by_id(snap.service_name)
        if snap is None:
            return GenericJobButationReturn(
                success=False,
                code=400,
                message=f"No such snapshot: {snapshot_id}",
                job=None,
            )

        job = add_restore_job(snap)
        restore_snapshot(snap)

        return GenericJobButationReturn(
            success=True,
            code=200,
            message="restore job created",
            job=job,
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def force_snapshots_reload(self) -> GenericMutationReturn:
        """Force snapshots reload"""
        Backups.force_snapshot_reload()
        return GenericMutationReturn(
            success=True,
            code=200,
            message="",
        )
