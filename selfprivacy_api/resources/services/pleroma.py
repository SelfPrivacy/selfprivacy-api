#!/usr/bin/env python3
from flask_restful import Resource

from selfprivacy_api.resources.services import api

# Enable Pleroma
class EnablePleroma(Resource):
    def post(self):
        readOnlyFileDescriptor = open("/etc/nixos/social/pleroma.nix", "rt")
        fileContent = readOnlyFileDescriptor.read()
        fileContent = fileContent.replace("enable = false;", "enable = true;")
        readOnlyFileDescriptor.close()
        readWriteFileDescriptor = open("/etc/nixos/social/pleroma.nix", "wt")
        writeOperationDescriptor = readWriteFileDescriptor.write(fileContent)
        readWriteFileDescriptor.close()

        return {
            "status": 0,
            "descriptor": writeOperationDescriptor,
            "message": "Pleroma enabled",
        }


# Disable Pleroma
class DisablePleroma(Resource):
    def post(self):
        readOnlyFileDescriptor = open("/etc/nixos/social/pleroma.nix", "rt")
        fileContent = readOnlyFileDescriptor.read()
        fileContent = fileContent.replace("enable = true;", "enable = false;")
        readOnlyFileDescriptor.close()
        readWriteFileDescriptor = open("/etc/nixos/social/pleroma.nix", "wt")
        writeOperationDescriptor = readWriteFileDescriptor.write(fileContent)
        readWriteFileDescriptor.close()

        return {
            "status": 0,
            "descriptor": writeOperationDescriptor,
            "message": "Pleroma disabled",
        }


api.add_resource(EnablePleroma, "/pleroma/enable")
api.add_resource(DisablePleroma, "/pleroma/disable")
