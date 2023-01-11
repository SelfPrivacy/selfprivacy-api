import json
from datetime import datetime, timezone, timedelta
from mnemonic import Mnemonic

# for expiration tests. If headache, consider freezegun
RECOVERY_KEY_VALIDATION_DATETIME = "selfprivacy_api.models.tokens.time.datetime"
DEVICE_KEY_VALIDATION_DATETIME = RECOVERY_KEY_VALIDATION_DATETIME

FIVE_MINUTES_INTO_FUTURE_NAIVE = datetime.now() + timedelta(minutes=5)
FIVE_MINUTES_INTO_FUTURE = datetime.now(timezone.utc) + timedelta(minutes=5)
FIVE_MINUTES_INTO_PAST_NAIVE = datetime.now() - timedelta(minutes=5)
FIVE_MINUTES_INTO_PAST = datetime.now(timezone.utc) - timedelta(minutes=5)


class NearFuture(datetime):
    @classmethod
    def now(cls, tz=None):
        return datetime.now(tz) + timedelta(minutes=13)


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


def mnemonic_to_hex(mnemonic):
    return Mnemonic(language="english").to_entropy(mnemonic).hex()


def assert_recovery_recent(time_generated):
    assert (
        datetime.strptime(time_generated, "%Y-%m-%dT%H:%M:%S.%f") - timedelta(seconds=5)
        < datetime.now()
    )
