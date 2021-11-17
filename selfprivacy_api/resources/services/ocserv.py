#!/usr/bin/env python3
"""OpenConnect VPN server management module"""
import json
import portalocker
from flask_restful import Resource

from selfprivacy_api.resources.services import api


class EnableOcserv(Resource):
    """Enable OpenConnect VPN server"""

    def post(self):
        """
        Enable OCserv
        ---
        tags:
            - OCserv
        security:
            - bearerAuth: []
        responses:
            200:
                description: OCserv enabled
            401:
                description: Unauthorized
        """
        with open(
            "/etc/nixos/userdata/userdata.json", "r+", encoding="utf-8"
        ) as userdata_file:
            portalocker.lock(userdata_file, portalocker.LOCK_EX)
            try:
                data = json.load(userdata_file)
                if "ocserv" not in data:
                    data["ocserv"] = {}
                data["ocserv"]["enable"] = True
                userdata_file.seek(0)
                json.dump(data, userdata_file, indent=4)
                userdata_file.truncate()
            finally:
                portalocker.unlock(userdata_file)

        return {
            "status": 0,
            "message": "OpenConnect VPN server enabled",
        }


class DisableOcserv(Resource):
    """Disable OpenConnect VPN server"""

    def post(self):
        """
        Disable OCserv
        ---
        tags:
            - OCserv
        security:
            - bearerAuth: []
        responses:
            200:
                description: OCserv disabled
            401:
                description: Unauthorized
        """
        with open(
            "/etc/nixos/userdata/userdata.json", "r+", encoding="utf-8"
        ) as userdata_file:
            portalocker.lock(userdata_file, portalocker.LOCK_EX)
            try:
                data = json.load(userdata_file)
                if "ocserv" not in data:
                    data["ocserv"] = {}
                data["ocserv"]["enable"] = False
                userdata_file.seek(0)
                json.dump(data, userdata_file, indent=4)
                userdata_file.truncate()
            finally:
                portalocker.unlock(userdata_file)

        return {
            "status": 0,
            "message": "OpenConnect VPN server disabled",
        }


api.add_resource(EnableOcserv, "/ocserv/enable")
api.add_resource(DisableOcserv, "/ocserv/disable")
