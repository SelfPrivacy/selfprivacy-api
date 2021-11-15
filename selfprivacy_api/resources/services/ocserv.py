#!/usr/bin/env python3
from flask_restful import Resource
import portalocker
import json

from selfprivacy_api.resources.services import api

# Enable OpenConnect VPN server
class EnableOcserv(Resource):
    def post(self):
        with portalocker.Lock("/etc/nixos/userdata/userdata.json", "r+") as f:
            portalocker.lock(f, portalocker.LOCK_EX)
            try:
                data = json.load(f)
                if "ocserv" not in data:
                    data["ocserv"] = {}
                data["ocserv"]["enable"] = True
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
            finally:
                portalocker.unlock(f)

        return {
            "status": 0,
            "message": "OpenConnect VPN server enabled",
        }


# Disable OpenConnect VPN server
class DisableOcserv(Resource):
    def post(self):
        with portalocker.Lock("/etc/nixos/userdata/userdata.json", "r+") as f:
            portalocker.lock(f, portalocker.LOCK_EX)
            try:
                data = json.load(f)
                if "ocserv" not in data:
                    data["ocserv"] = {}
                data["ocserv"]["enable"] = False
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
            finally:
                portalocker.unlock(f)

        return {
            "status": 0,
            "message": "OpenConnect VPN server disabled",
        }


api.add_resource(EnableOcserv, "/ocserv/enable")
api.add_resource(DisableOcserv, "/ocserv/disable")
