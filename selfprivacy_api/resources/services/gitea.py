#!/usr/bin/env python3
"""Gitea management module"""
import json
import portalocker
from flask_restful import Resource

from selfprivacy_api.resources.services import api


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
        with open(
            "/etc/nixos/userdata/userdata.json", "r+", encoding="utf-8"
        ) as userdata_file:
            portalocker.lock(userdata_file, portalocker.LOCK_EX)
            try:
                data = json.load(userdata_file)
                if "gitea" not in data:
                    data["gitea"] = {}
                data["gitea"]["enable"] = True
                userdata_file.seek(0)
                json.dump(data, userdata_file, indent=4)
                userdata_file.truncate()
            finally:
                portalocker.unlock(userdata_file)

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
        with open(
            "/etc/nixos/userdata/userdata.json", "r+", encoding="utf-8"
        ) as userdata_file:
            portalocker.lock(userdata_file, portalocker.LOCK_EX)
            try:
                data = json.load(userdata_file)
                if "gitea" not in data:
                    data["gitea"] = {}
                data["gitea"]["enable"] = False
                userdata_file.seek(0)
                json.dump(data, userdata_file, indent=4)
                userdata_file.truncate()
            finally:
                portalocker.unlock(userdata_file)

        return {
            "status": 0,
            "message": "Gitea disabled",
        }


api.add_resource(EnableGitea, "/gitea/enable")
api.add_resource(DisableGitea, "/gitea/disable")
