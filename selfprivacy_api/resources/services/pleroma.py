#!/usr/bin/env python3
from flask_restful import Resource
import portalocker
import json

from selfprivacy_api.resources.services import api

# Enable Pleroma
class EnablePleroma(Resource):
    def post(self):
        with portalocker.Lock("/etc/nixos/userdata/userdata.json", "r+") as f:
            portalocker.lock(f, portalocker.LOCK_EX)
            try:
                data = json.load(f)
                if "pleroma" not in data:
                    data["pleroma"] = {}
                data["pleroma"]["enable"] = True
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
            finally:
                portalocker.unlock(f)

        return {
            "status": 0,
            "message": "Pleroma enabled",
        }


# Disable Pleroma
class DisablePleroma(Resource):
    def post(self):
        with portalocker.Lock("/etc/nixos/userdata/userdata.json", "r+") as f:
            portalocker.lock(f, portalocker.LOCK_EX)
            try:
                data = json.load(f)
                if "pleroma" not in data:
                    data["pleroma"] = {}
                data["pleroma"]["enable"] = False
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
            finally:
                portalocker.unlock(f)

        return {
            "status": 0,
            "message": "Pleroma disabled",
        }


api.add_resource(EnablePleroma, "/pleroma/enable")
api.add_resource(DisablePleroma, "/pleroma/disable")
