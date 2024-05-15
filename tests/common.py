import json
from datetime import datetime, timezone, timedelta
from mnemonic import Mnemonic

from selfprivacy_api.jobs import Job, JobStatus

# for expiration tests. If headache, consider freezegun
RECOVERY_KEY_VALIDATION_DATETIME = "selfprivacy_api.models.tokens.time.datetime"
DEVICE_KEY_VALIDATION_DATETIME = RECOVERY_KEY_VALIDATION_DATETIME


def ten_hours_into_future_naive():
    return datetime.now() + timedelta(hours=10)


def ten_hours_into_future_naive_utc():
    return datetime.utcnow() + timedelta(hours=10)


def ten_hours_into_future():
    return datetime.now(timezone.utc) + timedelta(hours=10)


def ten_minutes_into_past_naive():
    return datetime.now() - timedelta(minutes=10)


def ten_minutes_into_past_naive_utc():
    return datetime.utcnow() - timedelta(minutes=10)


def ten_minutes_into_past():
    return datetime.now(timezone.utc) - timedelta(minutes=10)


class NearFuture(datetime):
    @classmethod
    def now(cls, tz=None):
        return datetime.now(tz) + timedelta(hours=13)

    @classmethod
    def utcnow(cls):
        return datetime.utcnow() + timedelta(hours=13)


def read_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def write_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def generate_api_query(query_array):
    return "query TestApi {\n api {" + "\n".join(query_array) + "}\n}"


def generate_system_query(query_array):
    return "query TestSystem {\n system {" + "\n".join(query_array) + "}\n}"


def generate_users_query(query_array):
    return "query TestUsers {\n users {" + "\n".join(query_array) + "}\n}"


def generate_backup_query(query_array):
    return "query TestBackup {\n backup {" + "\n".join(query_array) + "}\n}"


def generate_jobs_query(query_array):
    return "query TestJobs {\n jobs {" + "\n".join(query_array) + "}\n}"


def generate_service_query(query_array):
    return "query TestService {\n services {" + "\n".join(query_array) + "}\n}"


def mnemonic_to_hex(mnemonic):
    return Mnemonic(language="english").to_entropy(mnemonic).hex()


def assert_recovery_recent(time_generated: str):
    assert datetime.fromisoformat(time_generated) - timedelta(seconds=5) < datetime.now(
        timezone.utc
    )


def assert_job_errored(job: Job):
    assert job is not None
    assert job.status == JobStatus.ERROR

    # consider adding a useful error message to an errored-out job
    assert job.error is not None
    assert job.error != ""
