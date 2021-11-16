#!/usr/bin/env python3
"""Nextcloud management module"""
import json
import portalocker
from flask_restful import Resource

from selfprivacy_api.resources.services import api


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
        with open(
            "/etc/nixos/userdata/userdata.json", "r+", encoding="utf-8"
        ) as userdata_file:
            portalocker.lock(userdata_file, portalocker.LOCK_EX)
            try:
                data = json.load(userdata_file)
                if "nextcloud" not in data:
                    data["nextcloud"] = {}
                data["nextcloud"]["enable"] = True
                userdata_file.seek(0)
                json.dump(data, userdata_file, indent=4)
                userdata_file.truncate()
            finally:
                portalocker.unlock(userdata_file)

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
        with open(
            "/etc/nixos/userdata/userdata.json", "r+", encoding="utf-8"
        ) as userdata_file:
            portalocker.lock(userdata_file, portalocker.LOCK_EX)
            try:
                data = json.load(userdata_file)
                if "nextcloud" not in data:
                    data["nextcloud"] = {}
                data["nextcloud"]["enable"] = False
                userdata_file.seek(0)
                json.dump(data, userdata_file, indent=4)
                userdata_file.truncate()
            finally:
                portalocker.unlock(userdata_file)

        return {
            "status": 0,
            "message": "Nextcloud disabled",
        }


api.add_resource(EnableNextcloud, "/nextcloud/enable")
api.add_resource(DisableNextcloud, "/nextcloud/disable")
