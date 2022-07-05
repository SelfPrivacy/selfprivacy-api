import json
from mnemonic import Mnemonic

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

def mnemonic_to_hex(mnemonic):
    return Mnemonic(language="english").to_entropy(mnemonic).hex()
