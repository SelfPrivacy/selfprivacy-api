#!/usr/bin/env python3
from flask import Blueprint, request
from flask_restful import Resource, reqparse
import portalocker
import json

from selfprivacy_api.resources.services import api

# Enable SSH
class EnableSSH(Resource):
    def post(self):
        with portalocker.Lock("/etc/nixos/userdata/userdata.json", "r+") as f:
            portalocker.lock(f, portalocker.LOCK_EX)
            try:
                data = json.load(f)
                if "ssh" not in data:
                    data["ssh"] = {}
                data["ssh"]["enable"] = True
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
            finally:
                portalocker.unlock(f)

        return {
            "status": 0,
            "message": "SSH enabled",
        }


# Write new SSH key
class WriteSSHKey(Resource):
    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            "public_key", type=str, required=True, help="Key cannot be blank!"
        )
        args = parser.parse_args()

        publicKey = args["public_key"]

        with portalocker.Lock("/etc/nixos/userdata/userdata.json", "r+") as f:
            portalocker.lock(f, portalocker.LOCK_EX)
            try:
                data = json.load(f)
                if "ssh" not in data:
                    data["ssh"] = {}
                # Return 400 if key already in array
                for key in data["ssh"]["rootSshKeys"]:
                    if key == publicKey:
                        return {
                            "error": "Key already exists",
                        }, 400
                data["ssh"]["rootSshKeys"].append(publicKey)
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
            finally:
                portalocker.unlock(f)

        return {
            "status": 0,
            "message": "New SSH key successfully written",
        }


api.add_resource(EnableSSH, "/ssh/enable")
api.add_resource(WriteSSHKey, "/ssh/key/send")
