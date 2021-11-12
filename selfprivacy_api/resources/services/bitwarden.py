#!/usr/bin/env python3
from flask_restful import Resource

from selfprivacy_api.resources.services import api

# Enable Bitwarden
class EnableBitwarden(Resource):
    def post(self):
        readOnlyFileDescriptor = open("/etc/nixos/passmgr/bitwarden.nix", "rt")
        fileContent = readOnlyFileDescriptor.read()
        fileContent = fileContent.replace("enable = false;", "enable = true;")
        readOnlyFileDescriptor.close()
        readWriteFileDescriptor = open("/etc/nixos/passmgr/bitwarden.nix", "wt")
        writeOperationDescriptor = readWriteFileDescriptor.write(fileContent)
        readWriteFileDescriptor.close()

        return {
            "status": 0,
            "descriptor": writeOperationDescriptor,
            "message": "Bitwarden enabled",
        }


# Disable Bitwarden
class DisableBitwarden(Resource):
    def post(self):
        readOnlyFileDescriptor = open("/etc/nixos/passmgr/bitwarden.nix", "rt")
        fileContent = readOnlyFileDescriptor.read()
        fileContent = fileContent.replace("enable = true;", "enable = false;")
        readOnlyFileDescriptor.close()
        readWriteFileDescriptor = open("/etc/nixos/passmgr/bitwarden.nix", "wt")
        writeOperationDescriptor = readWriteFileDescriptor.write(fileContent)
        readWriteFileDescriptor.close()

        return {
            "status": 0,
            "descriptor": writeOperationDescriptor,
            "message": "Bitwarden disabled",
        }


api.add_resource(EnableBitwarden, "/bitwarden/enable")
api.add_resource(DisableBitwarden, "/bitwarden/disable")
