#!/usr/bin/env python3
"""New device auth module"""
from flask_restful import Resource, reqparse

from selfprivacy_api.resources.api_auth import api
from selfprivacy_api.utils.auth import (
    get_new_device_auth_token,
    use_new_device_auth_token,
    delete_new_device_auth_token,
)


class NewDevice(Resource):
    """New device auth class
    POST returns a new token for the caller.
    """

    def post(self):
        """
        Get new device token
        ---
        tags:
            - Tokens
        security:
            - bearerAuth: []
        responses:
            200:
                description: New device token
            400:
                description: Bad request
        """
        token = get_new_device_auth_token()
        return {"token": token}

    def delete(self):
        """
        Delete new device token
        ---
        tags:
            - Tokens
        security:
            - bearerAuth: []
        responses:
            200:
                description: New device token deleted
            400:
                description: Bad request
        """
        delete_new_device_auth_token()
        return {"token": None}


class AuthorizeDevice(Resource):
    """Authorize device class
    POST authorizes the caller.
    """

    def post(self):
        """
        Authorize device
        ---
        tags:
            - Tokens
        parameters:
            - in: body
              name: data
              required: true
              description: Who is authorizing
              schema:
                  type: object
                  properties:
                      token:
                          type: string
                          description: Mnemonic token to authorize
                      device:
                          type: string
                          description: Device to authorize
        responses:
            200:
                description: Device authorized
            400:
                description: Bad request
            404:
                description: Token not found
        """
        parser = reqparse.RequestParser()
        parser.add_argument(
            "token", type=str, required=True, help="Mnemonic token to authorize"
        )
        parser.add_argument(
            "device", type=str, required=True, help="Device to authorize"
        )
        args = parser.parse_args()
        auth_token = args["token"]
        device = args["device"]
        token = use_new_device_auth_token(auth_token, device)
        if token is None:
            return {"message": "Token not found"}, 404
        return {"message": "Device authorized", "token": token}, 200


api.add_resource(NewDevice, "/new_device")
api.add_resource(AuthorizeDevice, "/new_device/authorize")
