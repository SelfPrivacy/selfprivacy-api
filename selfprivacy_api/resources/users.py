#!/usr/bin/env python3
from flask import Blueprint, jsonify, request
from flask_restful import Resource, Api
import subprocess

from selfprivacy_api import resources

api_users = Blueprint("api_users", __name__)
api = Api(api_users)

# Create a new user
class Users(Resource):
    def post(self):
        rawPassword = request.headers.get("X-Password")
        hashingCommand = """
            mkpasswd -m sha-512 {0}
        """.format(
            rawPassword
        )
        passwordHashProcessDescriptor = subprocess.Popen(
            hashingCommand, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        hashedPassword = passwordHashProcessDescriptor.communicate()[0]
        hashedPassword = hashedPassword.decode("ascii")
        hashedPassword = hashedPassword.rstrip()

        print("[TRACE] {0}".format(hashedPassword))

        print("[INFO] Opening /etc/nixos/users.nix...", sep="")
        readOnlyFileDescriptor = open("/etc/nixos/users.nix", "r")
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

        userTemplate = """

        #begin
        \"{0}\" = {{
            isNormalUser = true;
            hashedPassword = \"{1}\";
        }};
        #end
        """.format(
            request.headers.get("X-User"), hashedPassword
        )

        mailUserTemplate = """
            \"{0}@{2}\" = {{
            hashedPassword = 
                \"{1}\";
            catchAll = [ \"{2}\" ];

            sieveScript = ''
            require [\"fileinto\", \"mailbox\"];
            if header :contains \"Chat-Version\" \"1.0\"
            {{     
                fileinto :create \"DeltaChat\";
                    stop;
            }}
            '';
            }};""".format(
            request.headers.get("X-User"),
            hashedPassword,
            request.headers.get("X-Domain"),
        )

        for line in fileContent:
            index += 1
            if line.startswith("      #begin"):
                print("[DEBUG] Found user configuration snippet match!")
                print(
                    "[INFO] Writing new user configuration snippet to memory...", sep=""
                )
                fileContent.insert(index - 1, userTemplate)
                print("done")
                break

        print("[INFO] Writing data from memory to file...", sep="")
        readWriteFileDescriptor = open("/etc/nixos/users.nix", "w")
        userConfigurationWriteOperationResult = readWriteFileDescriptor.writelines(
            fileContent
        )
        print("done")

        readOnlyFileDescriptor.close()
        readWriteFileDescriptor.close()

        print(
            "[INFO] Opening /etc/nixos/mailserver/system/mailserver.nix.nix for reading...",
            sep="",
        )
        readOnlyFileDescriptor = open("/etc/nixos/mailserver/system/mailserver.nix")
        print("done")

        fileContent = list()
        index = int(0)

        while True:
            line = readOnlyFileDescriptor.readline()

            if not line:
                break
            else:
                fileContent.append(line)
                print("[DEBUG] Read line!")

        for line in fileContent:
            if line.startswith("    loginAccounts = {"):
                print("[DEBUG] Found mailuser configuration snippet match!")
                print(
                    "[INFO] Writing new user configuration snippet to memory...", sep=""
                )
                fileContent.insert(index + 1, mailUserTemplate)
                print("done")
                break
            index += 1

        readWriteFileDescriptor = open(
            "/etc/nixos/mailserver/system/mailserver.nix", "w"
        )

        mailUserConfigurationWriteOperationResult = readWriteFileDescriptor.writelines(
            fileContent
        )

        return {
            "result": 0,
            "descriptor0": userConfigurationWriteOperationResult,
            "descriptor1": mailUserConfigurationWriteOperationResult,
        }

    def delete(self):
        user = subprocess.Popen(["userdel", request.headers.get("X-User")])
        user.communicate()[0]
        return user.returncode
