#!/usr/bin/env python3
"""Recovery token module"""
from datetime import datetime
from flask import request
from flask_restful import Resource, reqparse

from selfprivacy_api.resources.api_auth import api
from selfprivacy_api.utils.auth import (
    is_recovery_token_exists,
    is_recovery_token_valid,
    get_recovery_token_status,
    generate_recovery_token,
    use_mnemonic_recoverery_token,
)


class RecoveryToken(Resource):
    """Recovery token class
    GET returns the status of the recovery token.
    POST generates a new recovery token.
    """

    def get(self):
        """
        Get recovery token status
        ---
        tags:
            - Tokens
        security:
            - bearerAuth: []
        responses:
            200:
                description: Recovery token status
                schema:
                    type: object
                    properties:
                        exists:
                            type: boolean
                            description: Recovery token exists
                        valid:
                            type: boolean
                            description: Recovery token is valid
                        date:
                            type: string
                            description: Recovery token date
                        expiration:
                            type: string
                            description: Recovery token expiration date
                        uses_left:
                            type: integer
                            description: Recovery token uses left
            400:
                description: Bad request
        """
        if not is_recovery_token_exists():
            return {
                "exists": False,
                "valid": False,
                "date": None,
                "expiration": None,
                "uses_left": None,
            }
        status = get_recovery_token_status()
        if not is_recovery_token_valid():
            return {
                "exists": True,
                "valid": False,
                "date": status["date"],
                "expiration": status["expiration"],
                "uses_left": status["uses_left"],
            }
        return {
            "exists": True,
            "valid": True,
            "date": status["date"],
            "expiration": status["expiration"],
            "uses_left": status["uses_left"],
        }

    def post(self):
        """
        Generate recovery token
        ---
        tags:
            - Tokens
        security:
            - bearerAuth: []
        parameters:
            - in: body
                name: data
                required: true
                description: Token data
                schema:
                    type: object
                    properties:
                        expiration:
                            type: string
                            description: Token expiration date
                        uses:
                            type: integer
                            description: Token uses
        responses:
            200:
                description: Recovery token generated
                schema:
                    type: object
                    properties:
                        token:
                            type: string
                            description: Mnemonic recovery token
            400:
                description: Bad request
        """
        parser = reqparse.RequestParser()
        parser.add_argument(
            "expiration", type=str, required=True, help="Token expiration date"
        )
        parser.add_argument("uses", type=int, required=True, help="Token uses")
        args = parser.parse_args()
        # Convert expiration date to datetime and return 400 if it is not valid
        try:
            expiration = datetime.strptime(args["expiration"], "%Y-%m-%dT%H:%M:%S.%fZ")
        except ValueError:
            return {
                "error": "Invalid expiration date. Use YYYY-MM-DDTHH:MM:SS.SSSZ"
            }, 400
        # Generate recovery token
        token = generate_recovery_token(expiration, args["uses"])
        return {"token": token}


class UseRecoveryToken(Resource):
    """Use recovery token class
    POST uses the recovery token.
    """

    def post(self):
        """
        Use recovery token
        ---
        tags:
            - Tokens
        security:
            - bearerAuth: []
        parameters:
            - in: body
                name: data
                required: true
                description: Token data
                schema:
                    type: object
                    properties:
                        token:
                            type: string
                            description: Mnemonic recovery token
                        device:
                            type: string
                            description: Device to authorize
        responses:
            200:
                description: Recovery token used
                schema:
                    type: object
                    properties:
                        token:
                            type: string
                            description: Device authorization token
            400:
                description: Bad request
            404:
                description: Token not found
        """
        parser = reqparse.RequestParser()
        parser.add_argument(
            "token", type=str, required=True, help="Mnemonic recovery token"
        )
        parser.add_argument(
            "device", type=str, required=True, help="Device to authorize"
        )
        args = parser.parse_args()
        # Use recovery token
        token = use_mnemonic_recoverery_token(args["token"], args["device"])
        if token is None:
            return {"error": "Token not found"}, 404
        return {"token": token}


api.add_resource(RecoveryToken, "/recovery_token")
api.add_resource(UseRecoveryToken, "/recovery_token/use")
