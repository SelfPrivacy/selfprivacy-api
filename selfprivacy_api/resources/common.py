#!/usr/bin/env python3
from flask import Flask, jsonify, request, json
from flask_restful import Resource
import subprocess

from selfprivacy_api.utils import get_domain

# Decrypt disk
class DecryptDisk(Resource):
    def post(self):
        decryptionCommand = """
    echo -n {0} | cryptsetup luksOpen /dev/sdb decryptedVar""".format(
            request.headers.get("X-Decryption-Key")
        )

        decryptionService = subprocess.Popen(
            decryptionCommand, shell=True, stdout=subprocess.PIPE
        )
        decryptionService.communicate()
        return {"status": decryptionService.returncode}
