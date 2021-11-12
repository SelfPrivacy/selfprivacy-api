#!/usr/bin/env python3
from flask_restful import Resource

from selfprivacy_api.resources.services import api

# Enable OpenConnect VPN server
class EnableOcserv(Resource):
    def post(self):
        readOnlyFileDescriptor = open("/etc/nixos/vpn/ocserv.nix", "rt")
        fileContent = readOnlyFileDescriptor.read()
        fileContent = fileContent.replace("enable = false;", "enable = true;")
        readOnlyFileDescriptor.close()
        readWriteFileDescriptor = open("/etc/nixos/vpn/ocserv.nix", "wt")
        writeOperationDescriptor = readWriteFileDescriptor.write(fileContent)
        readWriteFileDescriptor.close()

        return {
            "status": 0,
            "descriptor": writeOperationDescriptor,
            "message": "OpenConnect VPN server enabled",
        }


# Disable OpenConnect VPN server
class DisableOcserv(Resource):
    def post(self):
        readOnlyFileDescriptor = open("/etc/nixos/vpn/ocserv.nix", "rt")
        fileContent = readOnlyFileDescriptor.read()
        fileContent = fileContent.replace("enable = true;", "enable = false;")
        readOnlyFileDescriptor.close()
        readWriteFileDescriptor = open("/etc/nixos/vpn/ocserv.nix", "wt")
        writeOperationDescriptor = readWriteFileDescriptor.write(fileContent)
        readWriteFileDescriptor.close()

        return {
            "status": 0,
            "descriptor": writeOperationDescriptor,
            "message": "OpenConnect VPN server disabled",
        }


api.add_resource(EnableOcserv, "/ocserv/enable")
api.add_resource(DisableOcserv, "/ocserv/disable")
