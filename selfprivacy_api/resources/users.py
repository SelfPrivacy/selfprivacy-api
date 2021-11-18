#!/usr/bin/env python3
"""Users management module"""
import subprocess
import json
import re
import portalocker
from flask_restful import Resource, reqparse


class Users(Resource):
    """Users management"""

    def get(self):
        """
        Get a list of users
        ---
        tags:
            - Users
        security:
            - bearerAuth: []
        responses:
            200:
                description: A list of users
            401:
                description: Unauthorized
        """
        with open(
            "/etc/nixos/userdata/userdata.json", "r", encoding="utf-8"
        ) as userdata_file:
            portalocker.lock(userdata_file, portalocker.LOCK_SH)
            try:
                data = json.load(userdata_file)
                users = []
                for user in data["users"]:
                    users.append(user["username"])
            finally:
                portalocker.unlock(userdata_file)
        return users

    def post(self):
        """
        Create a new user
        ---
        consumes:
            - application/json
        tags:
            - Users
        security:
            - bearerAuth: []
        parameters:
            - in: body
              name: user
              required: true
              description: User to create
              schema:
                type: object
                required:
                    - username
                    - password
                properties:
                    username:
                        type: string
                        description: Unix username. Must be alphanumeric and less than 32 characters
                    password:
                        type: string
                        description: Unix password.
        responses:
            201:
                description: Created user
            400:
                description: Bad request
            401:
                description: Unauthorized
            409:
                description: User already exists
        """
        parser = reqparse.RequestParser(bundle_errors=True)
        parser.add_argument("username", type=str, required=True)
        parser.add_argument("password", type=str, required=True)
        args = parser.parse_args()

        hashing_command = ["mkpasswd", "-m", "sha-512", args["password"]]
        password_hash_process_descriptor = subprocess.Popen(
            hashing_command,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        hashed_password = password_hash_process_descriptor.communicate()[0]
        hashed_password = hashed_password.decode("ascii")
        hashed_password = hashed_password.rstrip()

        # Check is username passes regex
        if not re.match(r"^[a-z_][a-z0-9_]+$", args["username"]):
            return {"error": "username must be alphanumeric"}, 400
        # Check if username less than 32 characters
        if len(args["username"]) > 32:
            return {"error": "username must be less than 32 characters"}, 400

        with open(
            "/etc/nixos/userdata/userdata.json", "r+", encoding="utf-8"
        ) as userdata_file:
            portalocker.lock(userdata_file, portalocker.LOCK_EX)
            try:
                data = json.load(userdata_file)

                if "users" not in data:
                    data["users"] = []

                # Return 400 if user already exists
                for user in data["users"]:
                    if user["username"] == args["username"]:
                        return {"error": "User already exists"}, 409

                data["users"].append(
                    {
                        "username": args["username"],
                        "hashedPassword": hashed_password,
                    }
                )
                userdata_file.seek(0)
                json.dump(data, userdata_file, indent=4)
                userdata_file.truncate()
            finally:
                portalocker.unlock(userdata_file)

        return {"result": 0, "username": args["username"]}, 201


class User(Resource):
    """Single user managment"""

    def delete(self, username):
        """
        Delete a user
        ---
        tags:
            - Users
        security:
            - bearerAuth: []
        parameters:
            - in: path
              name: username
              required: true
              description: User to delete
              type: string
        responses:
            200:
                description: Deleted user
            400:
                description: Bad request
            401:
                description: Unauthorized
            404:
                description: User not found
        """
        with open(
            "/etc/nixos/userdata/userdata.json", "r+", encoding="utf-8"
        ) as userdata_file:
            portalocker.lock(userdata_file, portalocker.LOCK_EX)
            try:
                data = json.load(userdata_file)
                # Return 400 if username is not provided
                if username is None:
                    return {"error": "username is required"}, 400
                if username == data["username"]:
                    return {"error": "Cannot delete root user"}, 400
                # Return 400 if user does not exist
                for user in data["users"]:
                    if user["username"] == username:
                        data["users"].remove(user)
                        break
                else:
                    return {"error": "User does not exist"}, 404

                userdata_file.seek(0)
                json.dump(data, userdata_file, indent=4)
                userdata_file.truncate()
            finally:
                portalocker.unlock(userdata_file)

        return {"result": 0, "username": username}
