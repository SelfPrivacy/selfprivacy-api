from typing import Optional, List

from selfprivacy_api.models.backup.snapshot import Snapshot
from selfprivacy_api.jobs import Jobs, Job, JobStatus
from selfprivacy_api.services.service import Service
from selfprivacy_api.services import ServiceManager


def job_type_prefix(service: Service) -> str:
    return f"services.{service.get_id()}"


def backup_job_type(service: Service) -> str:
    return f"{job_type_prefix(service)}.backup"


def autobackup_job_type() -> str:
    return "backups.autobackup"


def restore_job_type(service: Service) -> str:
    return f"{job_type_prefix(service)}.restore"


def get_jobs_by_service(service: Service) -> List[Job]:
    result = []
    for job in Jobs.get_jobs():
        if job.type_id.startswith(job_type_prefix(service)) and job.status in [
            JobStatus.CREATED,
            JobStatus.RUNNING,
        ]:
            result.append(job)
    return result


def is_something_running_for(service: Service) -> bool:
    running_jobs = [
        job for job in get_jobs_by_service(service) if job.status == JobStatus.RUNNING
    ]
    return len(running_jobs) != 0


def add_autobackup_job(services: List[Service]) -> Job:
    service_names = [s.get_display_name() for s in services]
    pretty_service_list: str = ", ".join(service_names)
    job = Jobs.add(
        type_id=autobackup_job_type(),
        name="Automatic backup",
        description=f"Scheduled backup for services: {pretty_service_list}",
    )
    return job


def add_backup_job(service: Service) -> Job:
    if is_something_running_for(service):
        message = (
            f"Cannot start a backup of {service.get_id()}, another operation is running: "
            + get_jobs_by_service(service)[0].type_id
        )
        raise ValueError(message)
    display_name = service.get_display_name()
    job = Jobs.add(
        type_id=backup_job_type(service),
        name=f"Backup {display_name}",
        description=f"Backing up {display_name}",
    )
    return job


def complain_about_service_operation_running(service: Service) -> str:
    message = f"Cannot start a restore of {service.get_id()}, another operation is running: {get_jobs_by_service(service)[0].type_id}"
    raise ValueError(message)


def add_total_restore_job() -> Job:
    for service in ServiceManager.get_enabled_services():
        ensure_nothing_runs_for(service)

    job = Jobs.add(
        type_id="backups.total_restore",
        name=f"Total restore",
        description="Restoring all enabled services",
    )
    return job


def ensure_nothing_runs_for(service: Service):
    if (
        # TODO: try removing the exception. Why would we have it?
        not isinstance(service, ServiceManager)
        and is_something_running_for(service) is True
    ):
        complain_about_service_operation_running(service)


def add_total_backup_job() -> Job:
    for service in ServiceManager.get_enabled_services():
        ensure_nothing_runs_for(service)

    job = Jobs.add(
        type_id="backups.total_backup",
        name=f"Total backup",
        description="Backing up all the enabled services",
    )
    return job


def add_restore_job(snapshot: Snapshot) -> Job:
    service = ServiceManager.get_service_by_id(snapshot.service_name)
    if service is None:
        raise ValueError(f"no such service: {snapshot.service_name}")
    if is_something_running_for(service):
        complain_about_service_operation_running(service)
    display_name = service.get_display_name()
    job = Jobs.add(
        type_id=restore_job_type(service),
        name=f"Restore {display_name}",
        description=f"Restoring {display_name} from {snapshot.id}",
    )
    return job


def get_job_by_type(type_id: str) -> Optional[Job]:
    for job in Jobs.get_jobs():
        if job.type_id == type_id and job.status in [
            JobStatus.CREATED,
            JobStatus.RUNNING,
        ]:
            return job
    return None


def get_failed_job_by_type(type_id: str) -> Optional[Job]:
    for job in Jobs.get_jobs():
        if job.type_id == type_id and job.status == JobStatus.ERROR:
            return job
    return None


def get_backup_job(service: Service) -> Optional[Job]:
    return get_job_by_type(backup_job_type(service))


def get_backup_fail(service: Service) -> Optional[Job]:
    return get_failed_job_by_type(backup_job_type(service))


def get_restore_job(service: Service) -> Optional[Job]:
    return get_job_by_type(restore_job_type(service))
