#!/usr/bin/env python3
from flask_restful import Resource
import portalocker
import json

from selfprivacy_api.resources.services import api

# Enable Nextcloud
class EnableNextcloud(Resource):
    def post(self):
        with portalocker.Lock("/etc/nixos/userdata/userdata.json", "r+") as f:
            portalocker.lock(f, portalocker.LOCK_EX)
            try:
                data = json.load(f)
                if "nextcloud" not in data:
                    data["nextcloud"] = {}
                data["nextcloud"]["enable"] = True
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
            finally:
                portalocker.unlock(f)

        return {
            "status": 0,
            "message": "Nextcloud enabled",
        }


# Disable Nextcloud
class DisableNextcloud(Resource):
    def post(self):
        with portalocker.Lock("/etc/nixos/userdata/userdata.json", "r+") as f:
            portalocker.lock(f, portalocker.LOCK_EX)
            try:
                data = json.load(f)
                if "nextcloud" not in data:
                    data["nextcloud"] = {}
                data["nextcloud"]["enable"] = False
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
            finally:
                portalocker.unlock(f)

        return {
            "status": 0,
            "message": "Nextcloud disabled",
        }


api.add_resource(EnableNextcloud, "/nextcloud/enable")
api.add_resource(DisableNextcloud, "/nextcloud/disable")
