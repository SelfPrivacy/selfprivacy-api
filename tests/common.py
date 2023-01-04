import json
import datetime
from mnemonic import Mnemonic

# for expiration tests. If headache, consider freezegun
RECOVERY_KEY_VALIDATION_DATETIME = "selfprivacy_api.models.tokens.recovery_key.datetime"
DEVICE_KEY_VALIDATION_DATETIME = "selfprivacy_api.models.tokens.new_device_key.datetime"


class NearFuture(datetime.datetime):
    @classmethod
    def now(cls):
        return datetime.datetime.now() + datetime.timedelta(minutes=13)


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
