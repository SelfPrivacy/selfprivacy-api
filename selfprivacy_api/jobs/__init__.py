"""
Jobs controller. It handles the jobs that are created by the user.
This is a singleton class holding the jobs list.
Jobs can be added and removed.
A single job can be updated.
A job is a dictionary with the following keys:
    - id: unique identifier of the job
    - name: name of the job
    - description: description of the job
    - status: status of the job
    - created_at: date of creation of the job
    - updated_at: date of last update of the job
    - finished_at: date of finish of the job
    - error: error message if the job failed
    - result: result of the job
"""
import typing
import datetime
from uuid import UUID
import uuid
from enum import Enum

from pydantic import BaseModel

from selfprivacy_api.utils.redis_pool import RedisPool

JOB_EXPIRATION_SECONDS = 10 * 24 * 60 * 60  # ten days


class JobStatus(Enum):
    """
    Status of a job.
    """

    CREATED = "CREATED"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    ERROR = "ERROR"


class Job(BaseModel):
    """
    Job class.
    """

    uid: UUID
    type_id: str
    name: str
    description: str
    status: JobStatus
    status_text: typing.Optional[str]
    progress: typing.Optional[int]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    finished_at: typing.Optional[datetime.datetime]
    error: typing.Optional[str]
    result: typing.Optional[str]


class Jobs:
    """
    Jobs class.
    """

    @staticmethod
    def reset() -> None:
        """
        Reset the jobs list.
        """
        jobs = Jobs.get_jobs()
        for job in jobs:
            Jobs.remove(job)

    @staticmethod
    def add(
        name: str,
        type_id: str,
        description: str,
        status: JobStatus = JobStatus.CREATED,
        status_text: str = "",
        progress: int = 0,
    ) -> Job:
        """
        Add a job to the jobs list.
        """
        job = Job(
            uid=uuid.uuid4(),
            name=name,
            type_id=type_id,
            description=description,
            status=status,
            status_text=status_text,
            progress=progress,
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            finished_at=None,
            error=None,
            result=None,
        )
        redis = RedisPool().get_connection()
        _store_job_as_hash(redis, _redis_key_from_uuid(job.uid), job)
        return job

    @staticmethod
    def remove(job: Job) -> None:
        """
        Remove a job from the jobs list.
        """
        Jobs.remove_by_uid(str(job.uid))

    @staticmethod
    def remove_by_uid(job_uuid: str) -> bool:
        """
        Remove a job from the jobs list.
        """
        redis = RedisPool().get_connection()
        key = _redis_key_from_uuid(job_uuid)
        if redis.exists(key):
            redis.delete(key)
            return True
        return False

    @staticmethod
    def update(
        job: Job,
        status: JobStatus,
        status_text: typing.Optional[str] = None,
        progress: typing.Optional[int] = None,
        name: typing.Optional[str] = None,
        description: typing.Optional[str] = None,
        error: typing.Optional[str] = None,
        result: typing.Optional[str] = None,
    ) -> Job:
        """
        Update a job in the jobs list.
        """
        if name is not None:
            job.name = name
        if description is not None:
            job.description = description
        if status_text is not None:
            job.status_text = status_text
        if progress is not None:
            job.progress = progress
        job.status = status
        job.updated_at = datetime.datetime.now()
        job.error = error
        job.result = result
        if status in (JobStatus.FINISHED, JobStatus.ERROR):
            job.finished_at = datetime.datetime.now()

        redis = RedisPool().get_connection()
        key = _redis_key_from_uuid(job.uid)
        if redis.exists(key):
            _store_job_as_hash(redis, key, job)
            if status in (JobStatus.FINISHED, JobStatus.ERROR):
                redis.expire(key, JOB_EXPIRATION_SECONDS)

        return job

    @staticmethod
    def get_job(uid: str) -> typing.Optional[Job]:
        """
        Get a job from the jobs list.
        """
        redis = RedisPool().get_connection()
        key = _redis_key_from_uuid(uid)
        if redis.exists(key):
            return _job_from_hash(redis, key)
        return None

    @staticmethod
    def get_jobs() -> typing.List[Job]:
        """
        Get the jobs list.
        """
        redis = RedisPool().get_connection()
        job_keys = redis.keys("jobs:*")
        jobs = []
        for job_key in job_keys:
            job = _job_from_hash(redis, job_key)
            if job is not None:
                jobs.append(job)
        return jobs

    @staticmethod
    def is_busy() -> bool:
        """
        Check if there is a job running.
        """
        for job in Jobs.get_jobs():
            if job.status == JobStatus.RUNNING:
                return True
        return False


def _redis_key_from_uuid(uuid_string):
    return "jobs:" + str(uuid_string)


def _store_job_as_hash(redis, redis_key, model):
    for key, value in model.dict().items():
        if isinstance(value, uuid.UUID):
            value = str(value)
        if isinstance(value, datetime.datetime):
            value = value.isoformat()
        if isinstance(value, JobStatus):
            value = value.value
        redis.hset(redis_key, key, str(value))


def _job_from_hash(redis, redis_key):
    if redis.exists(redis_key):
        job_dict = redis.hgetall(redis_key)
        for date in [
            "created_at",
            "updated_at",
            "finished_at",
        ]:
            if job_dict[date] != "None":
                job_dict[date] = datetime.datetime.fromisoformat(job_dict[date])
        for key in job_dict.keys():
            if job_dict[key] == "None":
                job_dict[key] = None

        return Job(**job_dict)
    return None
