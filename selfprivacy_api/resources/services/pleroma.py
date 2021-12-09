#!/usr/bin/env python3
"""Pleroma management module"""
from flask_restful import Resource

from selfprivacy_api.resources.services import api
from selfprivacy_api.utils import WriteUserData


class EnablePleroma(Resource):
    """Enable Pleroma"""

    def post(self):
        """
        Enable Pleroma
        ---
        tags:
            - Pleroma
        security:
            - bearerAuth: []
        responses:
            200:
                description: Pleroma enabled
            401:
                description: Unauthorized
        """
        with WriteUserData() as data:
            if "pleroma" not in data:
                data["pleroma"] = {}
            data["pleroma"]["enable"] = True

        return {
            "status": 0,
            "message": "Pleroma enabled",
        }


class DisablePleroma(Resource):
    """Disable Pleroma"""

    def post(self):
        """
        Disable Pleroma
        ---
        tags:
            - Pleroma
        security:
            - bearerAuth: []
        responses:
            200:
                description: Pleroma disabled
            401:
                description: Unauthorized
        """
        with WriteUserData() as data:
            if "pleroma" not in data:
                data["pleroma"] = {}
            data["pleroma"]["enable"] = False

        return {
            "status": 0,
            "message": "Pleroma disabled",
        }


api.add_resource(EnablePleroma, "/pleroma/enable")
api.add_resource(DisablePleroma, "/pleroma/disable")
