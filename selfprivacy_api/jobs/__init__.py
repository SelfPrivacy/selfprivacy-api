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
import asyncio
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
        status_text: typing.Optional[str],
        progress: typing.Optional[int],
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
        self.status_text = status_text or ""
        self.progress = progress or 0
        self.created_at = created_at
        self.updated_at = updated_at
        self.finished_at = finished_at
        self.error = error
        self.result = result

    def __str__(self) -> str:
        """
        Convert the job to a string.
        """
        return f"{self.name} - {self.status}"

    def __repr__(self) -> str:
        """
        Convert the job to a string.
        """
        return f"{self.name} - {self.status}"


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
        # Observers of the jobs list.
        self.observers = []

    def add_observer(self, observer: typing.Callable[[typing.List[Job]], None]) -> None:
        """
        Add an observer to the jobs list.
        """
        self.observers.append(observer)

    def remove_observer(self, observer: typing.Callable[[typing.List[Job]], None]) -> None:
        """
        Remove an observer from the jobs list.
        """
        self.observers.remove(observer)

    def _notify_observers(self) -> None:
        """
        Notify the observers of the jobs list.
        """
        for observer in self.observers:
            observer(self.jobs)

    def add(
        self, name: str, description: str, status: JobStatus = JobStatus.CREATED, status_text: str = "", progress: int = 0
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
        self.jobs.append(job)
        # Notify the observers.
        self._notify_observers()

        return job

    def remove(self, job: Job) -> None:
        """
        Remove a job from the jobs list.
        """
        self.jobs.remove(job)
        # Notify the observers.
        self._notify_observers()

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
        if status == JobStatus.FINISHED or status == JobStatus.ERROR:
            job.finished_at = datetime.datetime.now()

        # Notify the observers.
        self._notify_observers()

        return job

    def get_job(self, id: str) -> typing.Optional[Job]:
        """
        Get a job from the jobs list.
        """
        for job in self.jobs:
            if job.id == id:
                return job
        return None

    def get_jobs(self) -> typing.List[Job]:
        """
        Get the jobs list.
        """
        return self.jobs
