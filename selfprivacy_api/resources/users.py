#!/usr/bin/env python3
from flask import Blueprint, jsonify, request
from flask_restful import Resource, Api
import subprocess
import portalocker
import json
import re

from selfprivacy_api import resources

api_users = Blueprint("api_users", __name__)
api = Api(api_users)

# Create a new user
class Users(Resource):
    def post(self):
        rawPassword = request.headers.get("X-Password")
        hashingCommand = """
            mkpasswd -m sha-512 {0}
        """.format(
            rawPassword
        )
        passwordHashProcessDescriptor = subprocess.Popen(
            hashingCommand, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        hashedPassword = passwordHashProcessDescriptor.communicate()[0]
        hashedPassword = hashedPassword.decode("ascii")
        hashedPassword = hashedPassword.rstrip()

        with open("/etc/nixos/userdata/userdata.json", "r+", encoding="utf8") as f:
            portalocker.lock(f, portalocker.LOCK_EX)
            try:
                data = json.load(f)
                # Return 400 if username is not provided
                if request.headers.get("X-User") is None:
                    return {"error": "username is required"}, 400
                # Return 400 if password is not provided
                if request.headers.get("X-Password") is None:
                    return {"error": "password is required"}, 400
                # Check is username passes regex
                if not re.match(r"^[a-z_][a-z0-9_]+$", request.headers.get("X-User")):
                    return {"error": "username must be alphanumeric"}, 400
                # Check if username less than 32 characters
                if len(request.headers.get("X-User")) > 32:
                    return {"error": "username must be less than 32 characters"}, 400
                # Return 400 if user already exists
                for user in data["users"]:
                    if user["username"] == request.headers.get("X-User"):
                        return {"error": "User already exists"}, 400
                if "users" not in data:
                    data["users"] = []
                data["users"].append(
                    {
                        "username": request.headers.get("X-User"),
                        "hashedPassword": hashedPassword,
                    }
                )
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
            finally:
                portalocker.unlock(f)

        return {"result": 0}

    def delete(self):
        with open("/etc/nixos/userdata/userdata.json", "r+", encoding="utf8") as f:
            portalocker.lock(f, portalocker.LOCK_EX)
            try:
                data = json.load(f)
                # Return 400 if username is not provided
                if request.headers.get("X-User") is None:
                    return {"error": "username is required"}, 400
                # Return 400 if user does not exist
                for user in data["users"]:
                    if user["username"] == request.headers.get("X-User"):
                        data["users"].remove(user)
                        break
                else:
                    return {"error": "User does not exist"}, 400

                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
            finally:
                portalocker.unlock(f)

        return {"result": 0}
