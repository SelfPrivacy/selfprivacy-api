#!/usr/bin/env python3
"""App tokens management module"""
from flask import request
from flask_restful import Resource, reqparse

from selfprivacy_api.resources.api_auth import api
from selfprivacy_api.utils.auth import (
    delete_token,
    get_tokens_info,
    delete_token,
    refresh_token,
    is_token_valid,
)


class Tokens(Resource):
    """Token management class
    GET returns the list of active devices.
    DELETE invalidates token unless it is the last one or the caller uses this token.
    POST refreshes the token of the caller.
    """

    def get(self):
        """
        Get current device tokens
        ---
        tags:
            - Tokens
        security:
            - bearerAuth: []
        responses:
            200:
                description: List of tokens
            400:
                description: Bad request
        """
        return get_tokens_info()

    def delete(self):
        """
        Delete token
        ---
        tags:
            - Tokens
        security:
            - bearerAuth: []
        parameters:
            - in: body
                name: token
                required: true
                description: Token to delete
                schema:
                    type: object
                    properties:
                        token:
                            type: string
                            description: Token to delete
        responses:
            200:
                description: Token deleted
            400:
                description: Bad request
            404:
                description: Token not found
        """
        parser = reqparse.RequestParser()
        parser.add_argument("token", type=str, required=True, help="Token to delete")
        args = parser.parse_args()
        token = args["token"]
        if request.headers.get("Authorization") == f"Bearer {token}":
            return {"message": "Cannot delete caller's token"}, 400
        if not is_token_valid(token):
            return {"message": "Token not found"}, 404
        delete_token(token)
        return {"message": "Token deleted"}, 200

    def post(self):
        """
        Refresh token
        ---
        tags:
            - Tokens
        security:
            - bearerAuth: []
        responses:
            200:
                description: Token refreshed
            400:
                description: Bad request
            404:
                description: Token not found
        """
        # Get token from header
        token = request.headers.get("Authorization").split(" ")[1]
        if not is_token_valid(token):
            return {"message": "Token not found"}, 404
        return refresh_token(token)


api.add_resource(Tokens, "/tokens")
