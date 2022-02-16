from datetime import datetime
import os
import json
from pathlib import Path

from selfprivacy_api.migrations.migration import Migration
from selfprivacy_api.utils import TOKENS_FILE, ReadUserData


class CreateTokensJson(Migration):
    def get_migration_name(self):
        return "create_tokens_json"

    def get_migration_description(self):
        return """Selfprivacy API used a single token in userdata.json for authentication.
        This migration creates a new tokens.json file with the old token in it.
        This migration runs if the tokens.json file does not exist.
        Old token is located at ["api"]["token"] in userdata.json.
        tokens.json path is declared in TOKENS_FILE imported from utils.py
        tokens.json must have the following format:
        {
            "tokens": [
                {
                    "token": "token_string",
                    "name": "Master Token",
                    "date": "current date from str(datetime.now())",
                }
            ]
        }
        tokens.json must have 0600 permissions.
        """

    def is_migration_needed(self):
        return not os.path.exists(TOKENS_FILE)

    def migrate(self):
        try:
            print(f"Creating tokens.json file at {TOKENS_FILE}")
            with ReadUserData() as userdata:
                token = userdata["api"]["token"]
            # Touch tokens.json with 0600 permissions
            Path(TOKENS_FILE).touch(mode=0o600)
            # Write token to tokens.json
            structure = {
                "tokens": [
                    {
                        "token": token,
                        "name": "primary_token",
                        "date": str(datetime.now()),
                    }
                ]
            }
            with open(TOKENS_FILE, "w", encoding="utf-8") as tokens:
                json.dump(structure, tokens, indent=4)
            print("Done")
        except Exception as e:
            print(e)
            print("Error creating tokens.json")
