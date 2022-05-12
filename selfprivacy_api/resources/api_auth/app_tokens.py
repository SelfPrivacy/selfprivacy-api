#!/usr/bin/env python3
"""App tokens management module"""
from flask import request
from flask_restful import Resource, reqparse

from selfprivacy_api.resources.api_auth import api
from selfprivacy_api.utils.auth import (
    delete_token,
    get_tokens_info,
    is_token_name_exists,
    is_token_name_pair_valid,
    refresh_token,
    get_token_name,
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
        caller_name = get_token_name(request.headers.get("Authorization").split(" ")[1])
        tokens = get_tokens_info()
        # Retrun a list of tokens and if it is the caller's token
        # it will be marked with a flag
        return [
            {
                "name": token["name"],
                "date": token["date"],
                "is_caller": token["name"] == caller_name,
            }
            for token in tokens
        ]

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
              description: Token's name to delete
              schema:
                  type: object
                  properties:
                      token_name:
                          type: string
                          description: Token name to delete
                          required: true
        responses:
            200:
                description: Token deleted
            400:
                description: Bad request
            404:
                description: Token not found
        """
        parser = reqparse.RequestParser()
        parser.add_argument(
            "token_name", type=str, required=True, help="Token to delete"
        )
        args = parser.parse_args()
        token_name = args["token_name"]
        if is_token_name_pair_valid(
            token_name, request.headers.get("Authorization").split(" ")[1]
        ):
            return {"message": "Cannot delete caller's token"}, 400
        if not is_token_name_exists(token_name):
            return {"message": "Token not found"}, 404
        delete_token(token_name)
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
        new_token = refresh_token(token)
        if new_token is None:
            return {"message": "Token not found"}, 404
        return {"token": new_token}, 200


api.add_resource(Tokens, "/tokens")
