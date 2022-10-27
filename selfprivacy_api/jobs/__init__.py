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
import json
import uuid
from enum import Enum

from pydantic import BaseModel

from selfprivacy_api.utils import ReadUserData, UserDataFiles, WriteUserData


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
        with WriteUserData(UserDataFiles.JOBS) as user_data:
            user_data["jobs"] = []

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
        with WriteUserData(UserDataFiles.JOBS) as user_data:
            try:
                if "jobs" not in user_data:
                    user_data["jobs"] = []
                user_data["jobs"].append(json.loads(job.json()))
            except json.decoder.JSONDecodeError:
                user_data["jobs"] = [json.loads(job.json())]
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
        with WriteUserData(UserDataFiles.JOBS) as user_data:
            if "jobs" not in user_data:
                user_data["jobs"] = []
            for i, j in enumerate(user_data["jobs"]):
                if j["uid"] == job_uuid:
                    del user_data["jobs"][i]
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

        with WriteUserData(UserDataFiles.JOBS) as user_data:
            if "jobs" not in user_data:
                user_data["jobs"] = []
            for i, j in enumerate(user_data["jobs"]):
                if j["uid"] == str(job.uid):
                    user_data["jobs"][i] = json.loads(job.json())
                    break

        return job

    @staticmethod
    def get_job(uid: str) -> typing.Optional[Job]:
        """
        Get a job from the jobs list.
        """
        with ReadUserData(UserDataFiles.JOBS) as user_data:
            if "jobs" not in user_data:
                user_data["jobs"] = []
            for job in user_data["jobs"]:
                if job["uid"] == uid:
                    return Job(**job)
        return None

    @staticmethod
    def get_jobs() -> typing.List[Job]:
        """
        Get the jobs list.
        """
        with ReadUserData(UserDataFiles.JOBS) as user_data:
            try:
                if "jobs" not in user_data:
                    user_data["jobs"] = []
                return [Job(**job) for job in user_data["jobs"]]
            except json.decoder.JSONDecodeError:
                return []

    @staticmethod
    def is_busy() -> bool:
        """
        Check if there is a job running.
        """
        with ReadUserData(UserDataFiles.JOBS) as user_data:
            if "jobs" not in user_data:
                user_data["jobs"] = []
            for job in user_data["jobs"]:
                if job["status"] == JobStatus.RUNNING.value:
                    return True
        return False
