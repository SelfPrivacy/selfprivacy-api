#!/usr/bin/env python3
"""Nextcloud management module"""
from flask_restful import Resource

from selfprivacy_api.resources.services import api
from selfprivacy_api.utils import WriteUserData


class EnableNextcloud(Resource):
    """Enable Nextcloud"""

    def post(self):
        """
        Enable Nextcloud
        ---
        tags:
            - Nextcloud
        security:
            - bearerAuth: []
        responses:
            200:
                description: Nextcloud enabled
            401:
                description: Unauthorized
        """
        with WriteUserData() as data:
            if "nextcloud" not in data:
                data["nextcloud"] = {}
            data["nextcloud"]["enable"] = True

        return {
            "status": 0,
            "message": "Nextcloud enabled",
        }


class DisableNextcloud(Resource):
    """Disable Nextcloud"""

    def post(self):
        """
        Disable Nextcloud
        ---
        tags:
            - Nextcloud
        security:
            - bearerAuth: []
        responses:
            200:
                description: Nextcloud disabled
            401:
                description: Unauthorized
        """
        with WriteUserData() as data:
            if "nextcloud" not in data:
                data["nextcloud"] = {}
            data["nextcloud"]["enable"] = False

        return {
            "status": 0,
            "message": "Nextcloud disabled",
        }


api.add_resource(EnableNextcloud, "/nextcloud/enable")
api.add_resource(DisableNextcloud, "/nextcloud/disable")
