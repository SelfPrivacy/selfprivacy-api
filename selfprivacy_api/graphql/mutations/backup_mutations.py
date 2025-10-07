import typing
import gettext

import strawberry
from strawberry.types import Info

from selfprivacy_api.utils.graphql import api_job_mutation_error
from selfprivacy_api.utils.localization import TranslateSystemMessage as t

from selfprivacy_api.jobs import Jobs

from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.graphql.mutations.mutation_interface import (
    GenericMutationReturn,
    GenericJobMutationReturn,
    MutationReturnInterface,
)
from selfprivacy_api.graphql.queries.backup import BackupConfiguration
from selfprivacy_api.graphql.queries.backup import Backup
from selfprivacy_api.graphql.queries.providers import BackupProvider
from selfprivacy_api.graphql.common_types.jobs import job_to_api_job
from selfprivacy_api.graphql.common_types.backup import (
    AutobackupQuotasInput,
    RestoreStrategy,
)

from selfprivacy_api.backup import Backups
from selfprivacy_api.services import ServiceManager
from selfprivacy_api.backup.tasks import (
    start_backup,
    restore_snapshot,
    prune_autobackup_snapshots,
    full_restore,
    total_backup,
)
from selfprivacy_api.backup.jobs import (
    add_backup_job,
    add_restore_job,
    add_total_restore_job,
    add_total_backup_job,
)
from selfprivacy_api.backup.local_secret import LocalBackupSecret

_ = gettext.gettext

RESTORE_JOB_CREATED = _("Restore job created")
NONEXISTENT_SERVICE = _("Nonexistent service:")
SNAPSHOT_NOT_FOUND = _("Snapshot not found with id:")


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
    # For migration. If set, no new secret is generated
    local_secret: typing.Optional[str] = None


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
            kind=repository.provider,
            login=repository.login,
            key=repository.password,
            location=repository.location_name,
            repo_id=repository.location_id,
        )

        secret = repository.local_secret
        if secret is not None:
            LocalBackupSecret.set(secret)
            Backups.force_snapshot_cache_reload()
        else:
            Backups.init_repo()
        return GenericBackupConfigReturn(
            success=True,
            message="",
            code=200,
            configuration=Backup().configuration(),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def remove_repository(self) -> GenericBackupConfigReturn:
        """Remove repository"""

        Backups.reset()
        return GenericBackupConfigReturn(
            success=True,
            message="",
            code=200,
            configuration=Backup().configuration(),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def set_autobackup_period(
        self, period: typing.Optional[int] = None
    ) -> GenericBackupConfigReturn:
        """Set autobackup period. None is to disable autobackup"""

        if period is not None:
            Backups.set_autobackup_period_minutes(period)
        else:
            Backups.set_autobackup_period_minutes(0)

        return GenericBackupConfigReturn(
            success=True,
            message="",
            code=200,
            configuration=Backup().configuration(),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def set_autobackup_quotas(
        self, quotas: AutobackupQuotasInput, info: Info
    ) -> GenericBackupConfigReturn:
        """
        Set autobackup quotas.
        Values <=0 for any timeframe mean no limits for that timeframe.
        To disable autobackup use autobackup period setting, not this mutation.
        """

        locale = info.context["locale"]
        job = Jobs.add(
            name=t.translate(text=_("Trimming autobackup snapshots"), locale=locale),
            type_id="backups.autobackup_trimming",
            description=t.translate(
                text=_(
                    "Pruning the excessive snapshots after the new autobackup quotas are set"
                ),
                locale=locale,
            ),
        )

        try:
            Backups.set_autobackup_quotas(quotas)
            # this task is async and can fail with only a job to report the error
            prune_autobackup_snapshots(job)
            return GenericBackupConfigReturn(
                success=True,
                message="",
                code=200,
                configuration=Backup().configuration(),
            )

        except Exception as e:
            return GenericBackupConfigReturn(
                success=False,
                message=type(e).__name__ + ":" + str(e),
                code=400,
                configuration=Backup().configuration(),
            )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def start_backup(self, service_id: str, info: Info) -> GenericJobMutationReturn:
        """Start backup"""

        locale = info.context["locale"]
        service = ServiceManager.get_service_by_id(service_id)
        if service is None:
            return GenericJobMutationReturn(
                success=False,
                code=300,
                message=f"{t.translate(text=NONEXISTENT_SERVICE, locale=locale)} {service_id}",
                job=None,
            )

        job = add_backup_job(service)
        start_backup(service_id)

        return GenericJobMutationReturn(
            success=True,
            code=200,
            message=t.translate(text=_("Backup job queued"), locale=locale),
            job=job_to_api_job(job),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def total_backup(self, info: Info) -> GenericJobMutationReturn:
        """
        Back up all the enabled services at once
        Useful when migrating
        """

        locale = info.context["locale"]
        try:
            job = add_total_backup_job()
            total_backup(job)
        except Exception as error:
            return api_job_mutation_error(error)

        return GenericJobMutationReturn(
            success=True,
            code=200,
            message=t.translate(text=_("Total backup task queued"), locale=locale),
            job=job_to_api_job(job),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def restore_all(self, info: Info) -> GenericJobMutationReturn:
        """
        Restore all restorable and enabled services according to last autobackup snapshots
        This happens in sync with partial merging of old configuration for compatibility
        """

        locale = info.context["locale"]
        try:
            job = add_total_restore_job()
            full_restore(job)
        except Exception as error:
            return GenericJobMutationReturn(
                success=False,
                code=400,
                message=str(error),
                job=None,
            )

        return GenericJobMutationReturn(
            success=True,
            code=200,
            message=t.translate(text=RESTORE_JOB_CREATED, locale=locale),
            job=job_to_api_job(job),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def restore_backup(
        self,
        snapshot_id: str,
        info: Info,
        strategy: RestoreStrategy = RestoreStrategy.DOWNLOAD_VERIFY_OVERWRITE,
    ) -> GenericJobMutationReturn:
        """Restore backup"""

        locale = info.context["locale"]
        snap = Backups.get_snapshot_by_id(snapshot_id)
        if snap is None:
            return GenericJobMutationReturn(
                success=False,
                code=404,
                message=f"{t.translate(text=SNAPSHOT_NOT_FOUND, locale=locale)} {snapshot_id}",
                job=None,
            )

        service = ServiceManager.get_service_by_id(snap.service_name)
        if service is None:
            return GenericJobMutationReturn(
                success=False,
                code=404,
                message=f"{t.translate(text=NONEXISTENT_SERVICE, locale=locale)} {snap.service_name}",
                job=None,
            )

        try:
            job = add_restore_job(snap)
        except ValueError as error:
            return GenericJobMutationReturn(
                success=False,
                code=400,
                message=str(error),
                job=None,
            )

        restore_snapshot(snap, strategy)

        return GenericJobMutationReturn(
            success=True,
            code=200,
            message=t.translate(text=RESTORE_JOB_CREATED, locale=locale),
            job=job_to_api_job(job),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def forget_snapshot(self, snapshot_id: str, info: Info) -> GenericMutationReturn:
        """Forget a snapshot.
        Makes it inaccessible from the server.
        After some time, the data (encrypted) will not be recoverable
        from the backup server too, but not immediately"""

        locale = info.context["locale"]
        snap = Backups.get_snapshot_by_id(snapshot_id)
        if snap is None:
            return GenericMutationReturn(
                success=False,
                code=404,
                message=f"{t.translate(text=SNAPSHOT_NOT_FOUND, locale=locale)} {snapshot_id}",
            )

        try:
            Backups.forget_snapshot(snap)
            return GenericMutationReturn(
                success=True,
                code=200,
                message="",
            )
        except Exception as error:
            return GenericMutationReturn(
                success=False,
                code=400,
                message=str(error),
            )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def force_snapshots_reload(self) -> GenericMutationReturn:
        """Force snapshots reload"""

        Backups.force_snapshot_cache_reload()
        return GenericMutationReturn(
            success=True,
            code=200,
            message="",
        )
