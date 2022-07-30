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
import json
import os
import time
import uuid
from enum import Enum


class JobStatus(Enum):
    """
    Status of a job.
    """

    CREATED = "CREATED"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    ERROR = "ERROR"


class Job:
    """
    Job class.
    """

    def __init__(
        self,
        name: str,
        description: str,
        status: JobStatus,
        created_at: datetime.datetime,
        updated_at: datetime.datetime,
        finished_at: typing.Optional[datetime.datetime],
        error: typing.Optional[str],
        result: typing.Optional[str],
    ):
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at
        self.finished_at = finished_at
        self.error = error
        self.result = result

    def to_dict(self) -> dict:
        """
        Convert the job to a dictionary.
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "finished_at": self.finished_at,
            "error": self.error,
            "result": self.result,
        }

    def to_json(self) -> str:
        """
        Convert the job to a JSON string.
        """
        return json.dumps(self.to_dict())

    def __str__(self) -> str:
        """
        Convert the job to a string.
        """
        return self.to_json()

    def __repr__(self) -> str:
        """
        Convert the job to a string.
        """
        return self.to_json()


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
        return Jobs.__instance

    def __init__(self):
        """
        Initialize the jobs list.
        """
        if Jobs.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            Jobs.__instance = self
        self.jobs = []

    def add(
        self, name: str, description: str, status: JobStatus = JobStatus.CREATED
    ) -> Job:
        """
        Add a job to the jobs list.
        """
        job = Job(
            name=name,
            description=description,
            status=status,
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            finished_at=None,
            error=None,
            result=None,
        )
        self.jobs.append(job)
        return job

    def remove(self, job: Job) -> None:
        """
        Remove a job from the jobs list.
        """
        self.jobs.remove(job)

    def update(
        self,
        job: Job,
        name: typing.Optional[str],
        description: typing.Optional[str],
        status: JobStatus,
        error: typing.Optional[str],
        result: typing.Optional[str],
    ) -> Job:
        """
        Update a job in the jobs list.
        """
        if name is not None:
            job.name = name
        if description is not None:
            job.description = description
        job.status = status
        job.updated_at = datetime.datetime.now()
        job.error = error
        job.result = result
        return job

    def get_job(self, id: str) -> typing.Optional[Job]:
        """
        Get a job from the jobs list.
        """
        for job in self.jobs:
            if job.id == id:
                return job
        return None

    def get_jobs(self) -> list:
        """
        Get the jobs list.
        """
        return self.jobs
