#!/usr/bin/env python3
"""Unassigned views"""
import subprocess
from flask_restful import Resource, reqparse


class ApiVersion(Resource):
    """SelfPrivacy API version"""

    def get(self):
        """Get API version
        ---
        tags:
            - System
        security:
            - bearerAuth: []
        responses:
            200:
                description: API version
                schema:
                    type: object
                    properties:
                        version:
                            type: string
                            description: API version
            401:
                description: Unauthorized
        """
        return {"version": "1.0.0"}


class DecryptDisk(Resource):
    """Decrypt disk"""

    def post(self):
        """
        Decrypt /dev/sdb using cryptsetup luksOpen
        ---
        consumes:
            - application/json
        tags:
            - System
        security:
            - bearerAuth: []
        parameters:
            - in: body
              name: body
              required: true
              description: Provide a password for decryption
              schema:
                type: object
                required:
                    - password
                properties:
                    password:
                        type: string
                        description: Decryption password.
        responses:
            201:
                description: OK
            400:
                description: Bad request
            401:
                description: Unauthorized
        """
        parser = reqparse.RequestParser(bundle_errors=True)
        parser.add_argument("password", type=str, required=True)
        args = parser.parse_args()

        decryption_command = ["cryptsetup", "luksOpen", "/dev/sdb", "decryptedVar"]

        # TODO: Check if this works at all

        decryption_service = subprocess.Popen(
            decryption_command,
            shell=False,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
        decryption_service.communicate(input=args["password"])
        return {"status": decryption_service.returncode}, 201
