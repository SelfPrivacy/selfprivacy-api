#!/usr/bin/env python3
"""Gitea management module"""
from flask_restful import Resource

from selfprivacy_api.resources.services import api
from selfprivacy_api.utils import WriteUserData


class EnableGitea(Resource):
    """Enable Gitea"""

    def post(self):
        """
        Enable Gitea
        ---
        tags:
            - Gitea
        security:
            - bearerAuth: []
        responses:
            200:
                description: Gitea enabled
            401:
                description: Unauthorized
        """
        with WriteUserData() as data:
            if "gitea" not in data:
                data["gitea"] = {}
            data["gitea"]["enable"] = True

        return {
            "status": 0,
            "message": "Gitea enabled",
        }


class DisableGitea(Resource):
    """Disable Gitea"""

    def post(self):
        """
        Disable Gitea
        ---
        tags:
            - Gitea
        security:
            - bearerAuth: []
        responses:
            200:
                description: Gitea disabled
            401:
                description: Unauthorized
        """
        with WriteUserData() as data:
            if "gitea" not in data:
                data["gitea"] = {}
            data["gitea"]["enable"] = False

        return {
            "status": 0,
            "message": "Gitea disabled",
        }


api.add_resource(EnableGitea, "/gitea/enable")
api.add_resource(DisableGitea, "/gitea/disable")
