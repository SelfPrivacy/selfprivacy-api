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
    - created_at: date of creation of the job, naive localtime
    - updated_at: date of last update of the job, naive localtime
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

STATUS_LOGS_PREFIX = "jobs_logs:status:"
PROGRESS_LOGS_PREFIX = "jobs_logs:progress:"


class JobStatus(str, Enum):
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
        Jobs.reset_logs()

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
    def reset_logs() -> None:
        redis = RedisPool().get_connection()
        for key in redis.keys(STATUS_LOGS_PREFIX + "*"):
            redis.delete(key)

    @staticmethod
    def log_status_update(job: Job, status: JobStatus) -> None:
        redis = RedisPool().get_connection()
        key = _status_log_key_from_uuid(job.uid)
        redis.lpush(key, status.value)
        redis.expire(key, 10)

    @staticmethod
    def log_progress_update(job: Job, progress: int) -> None:
        redis = RedisPool().get_connection()
        key = _progress_log_key_from_uuid(job.uid)
        redis.lpush(key, progress)
        redis.expire(key, 10)

    @staticmethod
    def status_updates(job: Job) -> list[JobStatus]:
        result: list[JobStatus] = []

        redis = RedisPool().get_connection()
        key = _status_log_key_from_uuid(job.uid)
        if not redis.exists(key):
            return []

        status_strings: list[str] = redis.lrange(key, 0, -1)  # type: ignore
        for status in status_strings:
            try:
                result.append(JobStatus[status])
            except KeyError as error:
                raise ValueError("impossible job status: " + status) from error
        return result

    @staticmethod
    def progress_updates(job: Job) -> list[int]:
        result: list[int] = []

        redis = RedisPool().get_connection()
        key = _progress_log_key_from_uuid(job.uid)
        if not redis.exists(key):
            return []

        progress_strings: list[str] = redis.lrange(key, 0, -1)  # type: ignore
        for progress in progress_strings:
            try:
                result.append(int(progress))
            except KeyError as error:
                raise ValueError("impossible job progress: " + progress) from error
        return result

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

        # if it is finished it is 100
        # unless user says otherwise
        if status == JobStatus.FINISHED and progress is None:
            progress = 100
        if progress is not None and job.progress != progress:
            job.progress = progress
            Jobs.log_progress_update(job, progress)

        job.status = status
        Jobs.log_status_update(job, status)
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
    def set_expiration(job: Job, expiration_seconds: int) -> Job:
        redis = RedisPool().get_connection()
        key = _redis_key_from_uuid(job.uid)
        if redis.exists(key):
            redis.expire(key, expiration_seconds)
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


def _redis_key_from_uuid(uuid_string) -> str:
    return "jobs:" + str(uuid_string)


def _status_log_key_from_uuid(uuid_string) -> str:
    return STATUS_LOGS_PREFIX + str(uuid_string)


def _progress_log_key_from_uuid(uuid_string) -> str:
    return PROGRESS_LOGS_PREFIX + str(uuid_string)


def _store_job_as_hash(redis, redis_key, model) -> None:
    for key, value in model.dict().items():
        if isinstance(value, uuid.UUID):
            value = str(value)
        if isinstance(value, datetime.datetime):
            value = value.isoformat()
        if isinstance(value, JobStatus):
            value = value.value
        redis.hset(redis_key, key, str(value))


def _job_from_hash(redis, redis_key) -> typing.Optional[Job]:
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
