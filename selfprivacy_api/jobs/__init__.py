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
import asyncio
import json
import os
import time
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
    uid: UUID = uuid.uuid4()
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

    __instance = None

    @staticmethod
    def get_instance():
        """
        Singleton method.
        """
        if Jobs.__instance is None:
            Jobs()
            if Jobs.__instance is None:
                raise Exception("Couldn't init Jobs singleton!")
            return Jobs.__instance
        return Jobs.__instance

    def __init__(self):
        """
        Initialize the jobs list.
        """
        if Jobs.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            Jobs.__instance = self

    def reset(self) -> None:
        """
        Reset the jobs list.
        """
        with WriteUserData(UserDataFiles.JOBS) as user_data:
            user_data = []

    def add(
        self,
        name: str,
        description: str,
        status: JobStatus = JobStatus.CREATED,
        status_text: str = "",
        progress: int = 0,
    ) -> Job:
        """
        Add a job to the jobs list.
        """
        job = Job(
            name=name,
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
                user_data.append(json.loads(job.json()))
            except json.decoder.JSONDecodeError:
                user_data = []
                user_data.append(json.loads(job.json()))
        return job

    def remove(self, job: Job) -> None:
        """
        Remove a job from the jobs list.
        """
        with WriteUserData(UserDataFiles.JOBS) as user_data:
            user_data = [x for x in user_data if x["uid"] != job.uid]

    def update(
        self,
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
            user_data = [x for x in user_data if x["uid"] != job.uid]
            user_data.append(json.loads(job.json()))

        return job

    def get_job(self, id: str) -> typing.Optional[Job]:
        """
        Get a job from the jobs list.
        """
        with ReadUserData(UserDataFiles.JOBS) as user_data:
            for job in user_data:
                if job["uid"] == id:
                    return Job(**job)
        return None

    def get_jobs(self) -> typing.List[Job]:
        """
        Get the jobs list.
        """
        with ReadUserData(UserDataFiles.JOBS) as user_data:
            try:
                return [Job(**job) for job in user_data]
            except json.decoder.JSONDecodeError:
                return []
