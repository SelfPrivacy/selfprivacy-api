#!/usr/bin/env python3
"""SSH management module"""
from flask_restful import Resource, reqparse

from selfprivacy_api.resources.services import api
from selfprivacy_api.utils import WriteUserData, ReadUserData, validate_ssh_public_key


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
        with WriteUserData() as data:
            if "ssh" not in data:
                data["ssh"] = {}
            data["ssh"]["enable"] = True

        return {
            "status": 0,
            "message": "SSH enabled",
        }


class SSHSettings(Resource):
    """Enable/disable SSH"""

    def get(self):
        """
        Get current SSH settings
        ---
        tags:
            - SSH
        security:
            - bearerAuth: []
        responses:
            200:
                description: SSH settings
            400:
                description: Bad request
        """
        with ReadUserData() as data:
            if "ssh" not in data:
                return {"enable": True, "passwordAuthentication": True}
            if "enable" not in data["ssh"]:
                data["ssh"]["enable"] = True
            if "passwordAuthentication" not in data["ssh"]:
                data["ssh"]["passwordAuthentication"] = True
            return {
                "enable": data["ssh"]["enable"],
                "passwordAuthentication": data["ssh"]["passwordAuthentication"],
            }

    def put(self):
        """
        Change SSH settings
        ---
        tags:
            - SSH
        security:
            - bearerAuth: []
        parameters:
            - name: sshSettings
              in: body
              required: true
              description: SSH settings
              schema:
                type: object
                required:
                    - enable
                    - passwordAuthentication
                properties:
                    enable:
                        type: boolean
                    passwordAuthentication:
                        type: boolean
        responses:
            200:
                description: New settings saved
            400:
                description: Bad request
        """
        parser = reqparse.RequestParser()
        parser.add_argument("enable", type=bool, required=False)
        parser.add_argument("passwordAuthentication", type=bool, required=False)
        args = parser.parse_args()
        enable = args["enable"]
        password_authentication = args["passwordAuthentication"]

        with WriteUserData() as data:
            if "ssh" not in data:
                data["ssh"] = {}
            if enable is not None:
                data["ssh"]["enable"] = enable
            if password_authentication is not None:
                data["ssh"]["passwordAuthentication"] = password_authentication

        return "SSH settings changed"


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

        if not validate_ssh_public_key(public_key):
            return {
                "error": "Invalid key type. Only ssh-ed25519 and ssh-rsa are supported.",
            }, 400

        with WriteUserData() as data:
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

        return {
            "status": 0,
            "message": "New SSH key successfully written",
        }, 201


class SSHKeys(Resource):
    """List SSH keys"""

    def get(self, username):
        """
        List SSH keys
        ---
        tags:
            - SSH
        security:
            - bearerAuth: []
        parameters:
            - in: path
              name: username
              type: string
              required: true
              description: User to list keys for
        responses:
            200:
                description: SSH keys
            401:
                description: Unauthorized
        """
        with ReadUserData() as data:
            if username == "root":
                if "ssh" not in data:
                    data["ssh"] = {}
                if "rootKeys" not in data["ssh"]:
                    data["ssh"]["rootKeys"] = []
                return data["ssh"]["rootKeys"]
            if username == data["username"]:
                if "sshKeys" not in data:
                    data["sshKeys"] = []
                return data["sshKeys"]
            if "users" not in data:
                data["users"] = []
            for user in data["users"]:
                if user["username"] == username:
                    if "sshKeys" not in user:
                        user["sshKeys"] = []
                    return user["sshKeys"]
            return {
                "error": "User not found",
            }, 404

    def post(self, username):
        """
        Add SSH key to the user
        ---
        tags:
            - SSH
        security:
            - bearerAuth: []
        parameters:
            - in: body
              required: true
              name: public_key
              schema:
                type: object
                required:
                    - public_key
                properties:
                    public_key:
                        type: string
            - in: path
              name: username
              type: string
              required: true
              description: User to add keys for
        responses:
            201:
                description: SSH key added
            401:
                description: Unauthorized
            404:
                description: User not found
            409:
                description: Key already exists
        """
        parser = reqparse.RequestParser()
        parser.add_argument(
            "public_key", type=str, required=True, help="Key cannot be blank!"
        )
        args = parser.parse_args()

        if username == "root":
            return {
                "error": "Use /ssh/key/send to add root keys",
            }, 400

        if not validate_ssh_public_key(args["public_key"]):
            return {
                "error": "Invalid key type. Only ssh-ed25519 and ssh-rsa are supported.",
            }, 400

        with WriteUserData() as data:
            if username == data["username"]:
                if "sshKeys" not in data:
                    data["sshKeys"] = []
                # Return 409 if key already in array
                for key in data["sshKeys"]:
                    if key == args["public_key"]:
                        return {
                            "error": "Key already exists",
                        }, 409
                data["sshKeys"].append(args["public_key"])
                return {
                    "message": "New SSH key successfully written",
                }, 201

            if "users" not in data:
                data["users"] = []
            for user in data["users"]:
                if user["username"] == username:
                    if "sshKeys" not in user:
                        user["sshKeys"] = []
                    # Return 409 if key already in array
                    for key in user["sshKeys"]:
                        if key == args["public_key"]:
                            return {
                                "error": "Key already exists",
                            }, 409
                    user["sshKeys"].append(args["public_key"])
                    return {
                        "message": "New SSH key successfully written",
                    }, 201
            return {
                "error": "User not found",
            }, 404

    def delete(self, username):
        """
        Delete SSH key
        ---
        tags:
            - SSH
        security:
            - bearerAuth: []
        parameters:
            - in: body
              name: public_key
              required: true
              description: Key to delete
              schema:
                type: object
                required:
                    - public_key
                properties:
                    public_key:
                        type: string
            - in: path
              name: username
              type: string
              required: true
              description: User to delete keys for
        responses:
            200:
                description: SSH key deleted
            401:
                description: Unauthorized
            404:
                description: Key not found
        """
        parser = reqparse.RequestParser()
        parser.add_argument(
            "public_key", type=str, required=True, help="Key cannot be blank!"
        )
        args = parser.parse_args()

        with WriteUserData() as data:
            if username == "root":
                if "ssh" not in data:
                    data["ssh"] = {}
                if "rootKeys" not in data["ssh"]:
                    data["ssh"]["rootKeys"] = []
                # Return 404 if key not in array
                for key in data["ssh"]["rootKeys"]:
                    if key == args["public_key"]:
                        data["ssh"]["rootKeys"].remove(key)
                        # If rootKeys became zero length, add empty string
                        if len(data["ssh"]["rootKeys"]) == 0:
                            data["ssh"]["rootKeys"].append("")
                        return {
                            "message": "SSH key deleted",
                        }, 200
                return {
                    "error": "Key not found",
                }, 404
            if username == data["username"]:
                if "sshKeys" not in data:
                    data["sshKeys"] = []
                # Return 404 if key not in array
                for key in data["sshKeys"]:
                    if key == args["public_key"]:
                        data["sshKeys"].remove(key)
                        return {
                            "message": "SSH key deleted",
                        }, 200
                return {
                    "error": "Key not found",
                }, 404
            if "users" not in data:
                data["users"] = []
            for user in data["users"]:
                if user["username"] == username:
                    if "sshKeys" not in user:
                        user["sshKeys"] = []
                    # Return 404 if key not in array
                    for key in user["sshKeys"]:
                        if key == args["public_key"]:
                            user["sshKeys"].remove(key)
                            return {
                                "message": "SSH key successfully deleted",
                            }, 200
                    return {
                        "error": "Key not found",
                    }, 404
        return {
            "error": "User not found",
        }, 404


api.add_resource(EnableSSH, "/ssh/enable")
api.add_resource(SSHSettings, "/ssh")

api.add_resource(WriteSSHKey, "/ssh/key/send")
api.add_resource(SSHKeys, "/ssh/keys/<string:username>")
