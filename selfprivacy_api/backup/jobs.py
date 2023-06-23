from typing import Optional, List

from selfprivacy_api.models.backup.snapshot import Snapshot
from selfprivacy_api.jobs import Jobs, Job, JobStatus
from selfprivacy_api.services.service import Service
from selfprivacy_api.services import get_service_by_id


def job_type_prefix(service: Service) -> str:
    return f"services.{service.get_id()}"


def backup_job_type(service: Service) -> str:
    return f"{job_type_prefix(service)}.backup"


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


def is_something_queued_for(service: Service) -> bool:
    return len(get_jobs_by_service(service)) != 0


def add_backup_job(service: Service) -> Job:
    if is_something_queued_for(service):
        message = (
            f"Cannot start a backup of {service.get_id()}, another operation is queued: "
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


def add_restore_job(snapshot: Snapshot) -> Job:
    service = get_service_by_id(snapshot.service_name)
    if service is None:
        raise ValueError(f"no such service: {snapshot.service_name}")
    if is_something_queued_for(service):
        message = (
            f"Cannot start a restore of {service.get_id()}, another operation is queued: "
            + get_jobs_by_service(service)[0].type_id
        )
        raise ValueError(message)
    display_name = service.get_display_name()
    job = Jobs.add(
        type_id=restore_job_type(service),
        name=f"Restore {display_name}",
        description=f"restoring {display_name} from {snapshot.id}",
    )
    return job


def get_job_by_type(type_id: str) -> Optional[Job]:
    for job in Jobs.get_jobs():
        if job.type_id == type_id and job.status in [
            JobStatus.CREATED,
            JobStatus.RUNNING,
        ]:
            return job


def get_backup_job(service: Service) -> Optional[Job]:
    return get_job_by_type(backup_job_type(service))


def get_restore_job(service: Service) -> Optional[Job]:
    return get_job_by_type(restore_job_type(service))
