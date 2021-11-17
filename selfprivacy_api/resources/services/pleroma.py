#!/usr/bin/env python3
"""Pleroma management module"""
import json
import portalocker
from flask_restful import Resource

from selfprivacy_api.resources.services import api


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
        with open(
            "/etc/nixos/userdata/userdata.json", "r+", encoding="utf-8"
        ) as userdata_file:
            portalocker.lock(userdata_file, portalocker.LOCK_EX)
            try:
                data = json.load(userdata_file)
                if "pleroma" not in data:
                    data["pleroma"] = {}
                data["pleroma"]["enable"] = True
                userdata_file.seek(0)
                json.dump(data, userdata_file, indent=4)
                userdata_file.truncate()
            finally:
                portalocker.unlock(userdata_file)

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
        with open(
            "/etc/nixos/userdata/userdata.json", "r+", encoding="utf-8"
        ) as userdata_file:
            portalocker.lock(userdata_file, portalocker.LOCK_EX)
            try:
                data = json.load(userdata_file)
                if "pleroma" not in data:
                    data["pleroma"] = {}
                data["pleroma"]["enable"] = False
                userdata_file.seek(0)
                json.dump(data, userdata_file, indent=4)
                userdata_file.truncate()
            finally:
                portalocker.unlock(userdata_file)

        return {
            "status": 0,
            "message": "Pleroma disabled",
        }


api.add_resource(EnablePleroma, "/pleroma/enable")
api.add_resource(DisablePleroma, "/pleroma/disable")
