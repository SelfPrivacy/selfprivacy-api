#!/usr/bin/env python3
from flask_restful import Resource
import base64
import subprocess

from selfprivacy_api.resources.services import api

from selfprivacy_api.utils import get_domain

# Get DKIM key from file
class DKIMKey(Resource):
    def get(self):
        domain = get_domain()
        catProcess = subprocess.Popen(
            ["cat", "/var/dkim/" + domain + ".selector.txt"], stdout=subprocess.PIPE
        )
        dkim = catProcess.communicate()[0]
        dkim = base64.b64encode(dkim)
        dkim = str(dkim, "utf-8")
        return dkim


api.add_resource(DKIMKey, "/mailserver/dkim")
