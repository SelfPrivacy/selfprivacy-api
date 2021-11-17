#!/usr/bin/env python3
"""Bitwarden management module"""
import json
import portalocker
from flask_restful import Resource

from selfprivacy_api.resources.services import api


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
        with open(
            "/etc/nixos/userdata/userdata.json", "r+", encoding="utf-8"
        ) as userdata_file:
            portalocker.lock(userdata_file, portalocker.LOCK_EX)
            try:
                data = json.load(userdata_file)
                if "bitwarden" not in data:
                    data["bitwarden"] = {}
                data["bitwarden"]["enable"] = True
                userdata_file.seek(0)
                json.dump(data, userdata_file, indent=4)
                userdata_file.truncate()
            finally:
                portalocker.unlock(userdata_file)

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
        with open(
            "/etc/nixos/userdata/userdata.json", "r+", encoding="utf-8"
        ) as userdata_file:
            portalocker.lock(userdata_file, portalocker.LOCK_EX)
            try:
                data = json.load(userdata_file)
                if "bitwarden" not in data:
                    data["bitwarden"] = {}
                data["bitwarden"]["enable"] = False
                userdata_file.seek(0)
                json.dump(data, userdata_file, indent=4)
                userdata_file.truncate()
            finally:
                portalocker.unlock(userdata_file)

        return {
            "status": 0,
            "message": "Bitwarden disabled",
        }


api.add_resource(EnableBitwarden, "/bitwarden/enable")
api.add_resource(DisableBitwarden, "/bitwarden/disable")
