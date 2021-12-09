#!/usr/bin/env python3
"""Mail server management module"""
import base64
import subprocess
import os
from flask_restful import Resource

from selfprivacy_api.resources.services import api

from selfprivacy_api.utils import get_domain


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

        if os.path.exists("/var/dkim/" + domain + ".selector.txt"):
            cat_process = subprocess.Popen(
                ["cat", "/var/dkim/" + domain + ".selector.txt"], stdout=subprocess.PIPE
            )
            dkim = cat_process.communicate()[0]
            dkim = base64.b64encode(dkim)
            dkim = str(dkim, "utf-8")
            return dkim
        return "DKIM file not found", 404


api.add_resource(DKIMKey, "/mailserver/dkim")
