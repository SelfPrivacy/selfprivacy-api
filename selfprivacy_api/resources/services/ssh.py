#!/usr/bin/env python3
from flask import Blueprint, request
from flask_restful import Resource

from selfprivacy_api.resources.services import api

# Enable SSH
class EnableSSH(Resource):
    def post(self):
        readOnlyFileDescriptor = open("/etc/nixos/configuration.nix", "rt")
        fileContent = readOnlyFileDescriptor.read()
        fileContent = fileContent.replace("enable = false;", "enable = true;")
        readOnlyFileDescriptor.close()
        readWriteFileDescriptor = open("/etc/nixos/configuration.nix", "wt")
        writeOperationDescriptor = readWriteFileDescriptor.write(fileContent)
        readWriteFileDescriptor.close()

        return {
            "status": 0,
            "descriptor": writeOperationDescriptor,
            "message": "SSH enabled",
        }


# Write new SSH key
class WriteSSHKey(Resource):
    def put(self):
        requestBody = request.get_json()

        publicKey = requestBody.data(["public_key"])

        print("[INFO] Opening /etc/nixos/configuration.nix...", sep="")
        readOnlyFileDescriptor = open("/etc/nixos/configuration.nix", "r")
        print("done")
        fileContent = list()
        index = int(0)

        print("[INFO] Reading file content...", sep="")

        while True:
            line = readOnlyFileDescriptor.readline()

            if not line:
                break
            else:
                fileContent.append(line)
                print("[DEBUG] Read line!")

        for line in fileContent:
            index += 1
            if "openssh.authorizedKeys.keys = [" in line:
                print("[DEBUG] Found SSH key configuration snippet match!")
                print("[INFO] Writing new SSH key", sep="")
                fileContent.append(index, '\n      "' + publicKey + '"')
                print("done")
                break

        print("[INFO] Writing data from memory to file...", sep="")
        readWriteFileDescriptor = open("/etc/nixos/configuration.nix", "w")
        print("done")
        operationResult = readWriteFileDescriptor.writelines(fileContent)

        return {
            "status": 0,
            "descriptor": operationResult,
            "message": "New SSH key successfully written to /etc/nixos/configuration.nix",
        }


api.add_resource(EnableSSH, "/ssh/enable")
api.add_resource(WriteSSHKey, "/ssh/key/send")
