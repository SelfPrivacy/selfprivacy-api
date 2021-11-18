#!/usr/bin/env python3
"""SSH management module"""
import json
import portalocker
from flask_restful import Resource, reqparse

from selfprivacy_api.resources.services import api


class EnableSSH(Resource):
    """Enable SSH"""

    def post(self):
        """
        Enable SSH
        ---
        tags:
            - SSH
        security:
            - bearerAuth: []
        responses:
            200:
                description: SSH enabled
            401:
                description: Unauthorized
        """
        with open(
            "/etc/nixos/userdata/userdata.json", "r+", encoding="utf-8"
        ) as userdata_file:
            portalocker.lock(userdata_file, portalocker.LOCK_EX)
            try:
                data = json.load(userdata_file)
                if "ssh" not in data:
                    data["ssh"] = {}
                data["ssh"]["enable"] = True
                userdata_file.seek(0)
                json.dump(data, userdata_file, indent=4)
                userdata_file.truncate()
            finally:
                portalocker.unlock(userdata_file)

        return {
            "status": 0,
            "message": "SSH enabled",
        }


class WriteSSHKey(Resource):
    """Write new SSH key"""

    def put(self):
        """
        Add a SSH root key
        ---
        consumes:
            - application/json
        tags:
            - SSH
        security:
            - bearerAuth: []
        parameters:
            - in: body
              name: body
              required: true
              description: Public key to add
              schema:
                type: object
                required:
                    - public_key
                properties:
                    public_key:
                        type: string
                        description: ssh-ed25519 public key.
        responses:
            201:
                description: Key added
            400:
                description: Bad request
            401:
                description: Unauthorized
            409:
                description: Key already exists
        """
        parser = reqparse.RequestParser()
        parser.add_argument(
            "public_key", type=str, required=True, help="Key cannot be blank!"
        )
        args = parser.parse_args()

        public_key = args["public_key"]

        with open(
            "/etc/nixos/userdata/userdata.json", "r+", encoding="utf-8"
        ) as userdata_file:
            portalocker.lock(userdata_file, portalocker.LOCK_EX)
            try:
                data = json.load(userdata_file)
                if "ssh" not in data:
                    data["ssh"] = {}
                if "rootKeys" not in data["ssh"]:
                    data["ssh"]["rootKeys"] = []
                # Return 409 if key already in array
                for key in data["ssh"]["rootKeys"]:
                    if key == public_key:
                        return {
                            "error": "Key already exists",
                        }, 409
                data["ssh"]["rootKeys"].append(public_key)
                userdata_file.seek(0)
                json.dump(data, userdata_file, indent=4)
                userdata_file.truncate()
            finally:
                portalocker.unlock(userdata_file)

        return {
            "status": 0,
            "message": "New SSH key successfully written",
        }, 201


api.add_resource(EnableSSH, "/ssh/enable")
api.add_resource(WriteSSHKey, "/ssh/key/send")
