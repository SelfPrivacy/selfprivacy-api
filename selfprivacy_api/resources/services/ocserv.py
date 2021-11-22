#!/usr/bin/env python3
"""OpenConnect VPN server management module"""
from flask_restful import Resource

from selfprivacy_api.resources.services import api
from selfprivacy_api.utils import WriteUserData


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
        with WriteUserData() as data:
            if "ocserv" not in data:
                data["ocserv"] = {}
            data["ocserv"]["enable"] = True

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
        with WriteUserData() as data:
            if "ocserv" not in data:
                data["ocserv"] = {}
            data["ocserv"]["enable"] = False

        return {
            "status": 0,
            "message": "OpenConnect VPN server disabled",
        }


api.add_resource(EnableOcserv, "/ocserv/enable")
api.add_resource(DisableOcserv, "/ocserv/disable")
