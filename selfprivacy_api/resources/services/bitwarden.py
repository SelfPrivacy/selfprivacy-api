#!/usr/bin/env python3
from flask_restful import Resource
import portalocker
import json

from selfprivacy_api.resources.services import api

# Enable Bitwarden
class EnableBitwarden(Resource):
    def post(self):
        with open("/etc/nixos/userdata/userdata.json", "r+", encoding="utf8") as f:
            portalocker.lock(f, portalocker.LOCK_EX)
            try:
                data = json.load(f)
                if "bitwarden" not in data:
                    data["bitwarden"] = {}
                data["bitwarden"]["enable"] = True
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
            finally:
                portalocker.unlock(f)

        return {
            "status": 0,
            "message": "Bitwarden enabled",
        }


# Disable Bitwarden
class DisableBitwarden(Resource):
    def post(self):
        with open("/etc/nixos/userdata/userdata.json", "r+", encoding="utf8") as f:
            portalocker.lock(f, portalocker.LOCK_EX)
            try:
                data = json.load(f)
                if "bitwarden" not in data:
                    data["bitwarden"] = {}
                data["bitwarden"]["enable"] = False
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
            finally:
                portalocker.unlock(f)

        return {
            "status": 0,
            "message": "Bitwarden disabled",
        }


api.add_resource(EnableBitwarden, "/bitwarden/enable")
api.add_resource(DisableBitwarden, "/bitwarden/disable")
