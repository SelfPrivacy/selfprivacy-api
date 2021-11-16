#!/usr/bin/env python3
from flask_restful import Resource
import portalocker
import json

from selfprivacy_api.resources.services import api

# Enable Gitea
class EnableGitea(Resource):
    def post(self):
        with open("/etc/nixos/userdata/userdata.json", "r+", encoding="utf8") as f:
            portalocker.lock(f, portalocker.LOCK_EX)
            try:
                data = json.load(f)
                if "gitea" not in data:
                    data["gitea"] = {}
                data["gitea"]["enable"] = True
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
            finally:
                portalocker.unlock(f)

        return {
            "status": 0,
            "message": "Gitea enabled",
        }


# Disable Gitea
class DisableGitea(Resource):
    def post(self):
        with open("/etc/nixos/userdata/userdata.json", "r+", encoding="utf8") as f:
            portalocker.lock(f, portalocker.LOCK_EX)
            try:
                data = json.load(f)
                if "gitea" not in data:
                    data["gitea"] = {}
                data["gitea"]["enable"] = False
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
            finally:
                portalocker.unlock(f)

        return {
            "status": 0,
            "message": "Gitea disabled",
        }


api.add_resource(EnableGitea, "/gitea/enable")
api.add_resource(DisableGitea, "/gitea/disable")
