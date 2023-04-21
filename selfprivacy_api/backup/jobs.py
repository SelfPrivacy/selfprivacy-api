from typing import Optional

from selfprivacy_api.jobs import Jobs, Job, JobStatus
from selfprivacy_api.services.service import Service


def backup_job_type(service: Service):
    return f"services.{service.get_id()}.backup"


def add_backup_job(service: Service) -> Job:
    display_name = service.get_display_name()
    job = Jobs.add(
        type_id=backup_job_type(service),
        name=f"Backup {display_name}",
        description=f"Backing up {display_name}",
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
