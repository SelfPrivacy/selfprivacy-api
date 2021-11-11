#!/usr/bin/env python3
from flask_restful import Resource

from selfprivacy_api.resources.services import api

# Enable Gitea
class EnableGitea(Resource):
    def post(self):
        readOnlyFileDescriptor = open("/etc/nixos/git/gitea.nix", "rt")
        fileContent = readOnlyFileDescriptor.read()
        fileContent = fileContent.replace("enable = false;", "enable = true;")
        readOnlyFileDescriptor.close()
        readWriteFileDescriptor = open("/etc/nixos/git/gitea.nix", "wt")
        writeOperationDescriptor = readWriteFileDescriptor.write(fileContent)
        readWriteFileDescriptor.close()

        return {
            "status": 0,
            "descriptor": writeOperationDescriptor,
            "message": "Gitea enabled",
        }


# Disable Gitea
class DisableGitea(Resource):
    def post(self):
        readOnlyFileDescriptor = open("/etc/nixos/git/gitea.nix", "rt")
        fileContent = readOnlyFileDescriptor.read()
        fileContent = fileContent.replace("enable = true;", "enable = false;")
        readOnlyFileDescriptor.close()
        readWriteFileDescriptor = open("/etc/nixos/git/gitea.nix", "wt")
        writeOperationDescriptor = readWriteFileDescriptor.write(fileContent)
        readWriteFileDescriptor.close()

        return {
            "status": 0,
            "descriptor": writeOperationDescriptor,
            "message": "Gitea disabled",
        }


api.add_resource(EnableGitea, "/gitea/enable")
api.add_resource(DisableGitea, "/gitea/disable")
