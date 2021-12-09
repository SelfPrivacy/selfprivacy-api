#!/usr/bin/env python3
"""Bitwarden management module"""
from flask_restful import Resource

from selfprivacy_api.resources.services import api
from selfprivacy_api.utils import WriteUserData


class EnableBitwarden(Resource):
    """Enable Bitwarden"""

    def post(self):
        """
        Enable Bitwarden
        ---
        tags:
            - Bitwarden
        security:
            - bearerAuth: []
        responses:
            200:
                description: Bitwarden enabled
            401:
                description: Unauthorized
        """
        with WriteUserData() as data:
            if "bitwarden" not in data:
                data["bitwarden"] = {}
            data["bitwarden"]["enable"] = True

        return {
            "status": 0,
            "message": "Bitwarden enabled",
        }


class DisableBitwarden(Resource):
    """Disable Bitwarden"""

    def post(self):
        """
        Disable Bitwarden
        ---
        tags:
            - Bitwarden
        security:
            - bearerAuth: []
        responses:
            200:
                description: Bitwarden disabled
            401:
                description: Unauthorized
        """
        with WriteUserData() as data:
            if "bitwarden" not in data:
                data["bitwarden"] = {}
            data["bitwarden"]["enable"] = False

        return {
            "status": 0,
            "message": "Bitwarden disabled",
        }


api.add_resource(EnableBitwarden, "/bitwarden/enable")
api.add_resource(DisableBitwarden, "/bitwarden/disable")
