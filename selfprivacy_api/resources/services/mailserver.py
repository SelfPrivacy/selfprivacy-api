#!/usr/bin/env python3
"""Mail server management module"""
import base64
import subprocess
import os
from flask_restful import Resource

from selfprivacy_api.resources.services import api

from selfprivacy_api.utils import get_dkim_key, get_domain


class DKIMKey(Resource):
    """Get DKIM key from file"""

    def get(self):
        """
        Get DKIM key from file
        ---
        tags:
            - Email
        security:
            - bearerAuth: []
        responses:
            200:
                description: DKIM key encoded in base64
            401:
                description: Unauthorized
            404:
                description: DKIM key not found
        """
        domain = get_domain()

        dkim = get_dkim_key(domain)
        if dkim is None:
            return "DKIM file not found", 404
        dkim = base64.b64encode(dkim.encode("utf-8")).decode("utf-8")
        return dkim


api.add_resource(DKIMKey, "/mailserver/dkim")
