#!/usr/bin/env python3
from flask_restful import Resource

from selfprivacy_api.resources.services import api

# Enable Nextcloud
class EnableNextcloud(Resource):
    def post(self):
        readOnlyFileDescriptor = open("/etc/nixos/nextcloud/nextcloud.nix", "rt")
        fileContent = readOnlyFileDescriptor.read()
        fileContent = fileContent.replace("enable = false;", "enable = true;")
        readOnlyFileDescriptor.close()
        readWriteFileDescriptor = open("/etc/nixos/nextcloud/nextcloud.nix", "wt")
        writeOperationDescriptor = readWriteFileDescriptor.write(fileContent)
        readWriteFileDescriptor.close()

        return {
            "status": 0,
            "descriptor": writeOperationDescriptor,
            "message": "Nextcloud enabled",
        }


# Disable Nextcloud
class DisableNextcloud(Resource):
    def post(self):
        readOnlyFileDescriptor = open("/etc/nixos/nextcloud/nextcloud.nix", "rt")
        fileContent = readOnlyFileDescriptor.read()
        fileContent = fileContent.replace("enable = true;", "enable = false;")
        readOnlyFileDescriptor.close()
        readWriteFileDescriptor = open("/etc/nixos/nextcloud/nextcloud.nix", "wt")
        writeOperationDescriptor = readWriteFileDescriptor.write(fileContent)
        readWriteFileDescriptor.close()

        return {
            "status": 0,
            "descriptor": writeOperationDescriptor,
            "message": "Nextcloud disabled",
        }


api.add_resource(EnableNextcloud, "/nextcloud/enable")
api.add_resource(DisableNextcloud, "/nextcloud/disable")
