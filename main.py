#!/usr/bin/env python3
from flask import Flask, jsonify, request, json
from flask_restful import Resource, Api, reqparse
import base64
import pandas as pd
import ast
import subprocess
import os
import fileinput


app = Flask(__name__)
api = Api(app)


@app.route("/systemVersion", methods=["GET"])
def uname():
    uname = subprocess.check_output(["uname", "-arm"])
    return jsonify(uname)


@app.route("/getDKIM", methods=["GET"])
def getDkimKey():
    with open("/var/domain") as domainFile:
        domain = domainFile.readline()
        domain = domain.rstrip("\n")
    catProcess = subprocess.Popen(["cat", "/var/dkim/" + domain + ".selector.txt"], stdout=subprocess.PIPE)
    dkim = catProcess.communicate()[0]
    dkim = base64.b64encode(dkim)
    dkim = str(dkim, 'utf-8')
    print(dkim)
    response = app.response_class(
        response=json.dumps(dkim),
        status=200,
        mimetype='application/json'
    )
    return response


@app.route("/pythonVersion", methods=["GET"])
def getPythonVersion():
    pythonVersion = subprocess.check_output(["python","--version"])
    return jsonify(pythonVersion)


@app.route("/apply", methods=["GET"])
def rebuildSystem():
     rebuildResult = subprocess.Popen(["nixos-rebuild","switch"])
     rebuildResult.communicate()[0]
     return jsonify(
         status=rebuildResult.returncode
         )


@app.route("/rollback", methods=["GET"])
def rollbackSystem():
     rollbackResult = subprocess.Popen(["nixos-rebuild","switch","--rollback"])
     rollbackResult.communicate()[0]
     return jsonify(rollbackResult.returncode)


@app.route("/upgrade", methods=["GET"])
def upgradeSystem():
     upgradeResult = subprocess.Popen(["nixos-rebuild","switch","--upgrade"])
     upgradeResult.communicate()[0]
     return jsonify(
         status=upgradeResult.returncode
         )


@app.route("/createUser", methods=["POST"])
def createUser():
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
      """.format(request.headers.get("X-User"), request.headers.get("X-Password"))

    for line in fileContent:
        index += 1
        if line.startswith("      #begin"):
            print("[DEBUG] Found user configuration snippet match!")
            print("[INFO] Writing new user configuration snippet to memory...", sep="")
            fileContent.insert(index-1, userTemplate)
            print("done")
            break

    print("[INFO] Writing data from memory to file...", sep="")
    readWriteFileDescriptor = open("/etc/nixos/users.nix", "w")
    print("done")
    operationResult = readWriteFileDescriptor.writelines(fileContent)


    return jsonify(
        result=0,
        descriptor = operationResult
    )


@app.route("/deleteUser", methods=["DELETE"])
def deleteUser():
    user = subprocess.Popen(["userdel",request.headers.get("X-User")])
    user.communicate()[0]
    return jsonify(user.returncode)


@app.route("/serviceStatus", methods=["GET"])

def getServiceStatus():
    imapService = subprocess.Popen(["systemctl", "status", "dovecot2.service"])
    imapService.communicate()[0]
    smtpService = subprocess.Popen(["systemctl", "status", "postfix.service"])
    smtpService.communicate()[0]
    httpService = subprocess.Popen(["systemctl", "status", "nginx.service"])
    httpService.communicate()[0]
    return jsonify(
        imap=imapService.returncode,
        smtp=smtpService.returncode,
        http=httpService.returncode
    )


@app.route("/decryptDisk", methods=["POST"])
def requestDiskDecryption():

    decryptionCommand = '''
echo -n {0} | cryptsetup luksOpen /dev/sdb decryptedVar'''.format(request.headers.get("X-Decryption-Key"))

    decryptionService = subprocess.Popen(decryptionCommand, shell=True, stdout=subprocess.PIPE)
    decryptionService.communicate()
    return jsonify(
        status=decryptionService.returncode
    )


@app.route("/services/ssh/enable", methods=["POST"])

def enableSSH():
    readOnlyFileDescriptor = open("/etc/nixos/configuration.nix", "rt")
    

    fileContent = readOnlyFileDescriptor.read()

    fileContent = fileContent.replace("enabled = false;", "enabled = true;")     
    readOnlyFileDescriptor.close()

    readWriteFileDescriptor = open("/etc/nixos/configuration.nix", "wt") 

    readWriteFileDescriptor.write(fileContent)
    readWriteFileDescriptor.close()
    
    return jsonify(
        status=0
    )

# Bitwarden

@app.route("/services/bitwarden/enable", methods=["POST"])

def enableBitwarden():
    readOnlyFileDescriptor = open("/etc/nixos/passmgr/bitwarden.nix", "rt")
    readWriteFileDescriptor = open("/etc/nixos/passmgr/bitwarden.nix", "wt")

    for line in readOnlyFileDescriptor:
        readWriteFileDescriptor.write(line.replace("enable = false;", "enable = true;"))

    readWriteFileDescriptor.close()
    readOnlyFileDescriptor.close()

    return jsonify(
        status=0
    )

@app.route("/services/bitwarden/disable", methods=["POST"])

def disableBitwarden():
    readOnlyFileDescriptor = open("/etc/nixos/passmgr/bitwarden.nix", "rt")
    readWriteFileDescriptor = open("/etc/nixos/passmgr/bitwarden.nix", "wt")

    for line in readOnlyFileDescriptor:
        readWriteFileDescriptor.write(line.replace("enable = true;", "enable = false;"))

    readWriteFileDescriptor.close()
    readOnlyFileDescriptor.close()

    return jsonify(
        status=0
    )

#Gitea

@app.route("/services/gitea/disable", methods=["POST"])

def disableGitea():
    readOnlyFileDescriptor = open("/etc/nixos/git/gitea.nix", "rt")
    readWriteFileDescriptor = open("/etc/nixos/git/gitea.nix", "wt")

    for line in readOnlyFileDescriptor:
        readWriteFileDescriptor.write(line.replace("enable = true;", "enable = false;"))

    readWriteFileDescriptor.close()
    readOnlyFileDescriptor.close()

    return jsonify(
        status=0
    )

@app.route("/services/gitea/enable", methods=["POST"])

def enableGitea():
    readOnlyFileDescriptor = open("/etc/nixos/git/gitea.nix", "rt")
    readWriteFileDescriptor = open("/etc/nixos/git/gitea.nix", "wt")

    for line in readOnlyFileDescriptor:
        readWriteFileDescriptor.write(line.replace("enable = false;", "enable = true;"))

    readWriteFileDescriptor.close()
    readOnlyFileDescriptor.close()

    return jsonify(
        status=0
    )

#Nextcloud

@app.route("/services/nextcloud/disable", methods=["POST"])

def disableNextcloud():
    readOnlyFileDescriptor = open("/etc/nixos/nextcloud/nextcloud.nix", "rt")
    readWriteFileDescriptor = open("/etc/nixos/nextcloud/nextcloud.nix", "wt")

    for line in readOnlyFileDescriptor:
        readWriteFileDescriptor.write(line.replace("enable = true;", "enable = false;"))

    readWriteFileDescriptor.close()
    readOnlyFileDescriptor.close()

    return jsonify(
        status=0
    )

@app.route("/services/nextcloud/enable", methods=["POST"])

def enableNextcloud():
    readOnlyFileDescriptor = open("/etc/nixos/nextcloud/nextcloud.nix", "rt")
    readWriteFileDescriptor = open("/etc/nixos/nextcloud/nextcloud.nix", "wt")

    for line in readOnlyFileDescriptor:
        readWriteFileDescriptor.write(line.replace("enable = false;", "enable = true;"))

    readWriteFileDescriptor.close()
    readOnlyFileDescriptor.close()

    return jsonify(
        status=0
    )

#Pleroma

@app.route("/services/pleroma/disable", methods=["POST"])

def disablePleroma():
    readOnlyFileDescriptor = open("/etc/nixos/social/pleroma.nix", "rt")
    readWriteFileDescriptor = open("/etc/nixos/social/pleroma.nix", "wt")

    for line in readOnlyFileDescriptor:
        readWriteFileDescriptor.write(line.replace("enable = true;", "enable = false;"))

    readWriteFileDescriptor.close()
    readOnlyFileDescriptor.close()

    return jsonify(
        status=0
    )

@app.route("/services/pleroma/enable", methods=["POST"])

def enablePleroma():
    readOnlyFileDescriptor = open("/etc/nixos/social/pleroma.nix", "rt")
    readWriteFileDescriptor = open("/etc/nixos/social/pleroma.nix", "wt")

    for line in readOnlyFileDescriptor:
        readWriteFileDescriptor.write(line.replace("enable = false;", "enable = true;"))

    readWriteFileDescriptor.close()
    readOnlyFileDescriptor.close()

    return jsonify(
        status=0
    )

#Ocserv

@app.route("/services/ocserv/disable", methods=["POST"])

def disableOcserv():
    readOnlyFileDescriptor = open("/etc/nixos/vpn/ocserv.nix", "rt")
    readWriteFileDescriptor = open("/etc/nixos/vpn/ocserv.nix", "wt")

    for line in readOnlyFileDescriptor:
        readWriteFileDescriptor.write(line.replace("enable = true;", "enable = false;"))

    readWriteFileDescriptor.close()
    readOnlyFileDescriptor.close()

    return jsonify(
        status=0
    )

@app.route("/services/ocserv/enable", methods=["POST"])

def enableOcserv():
    readOnlyFileDescriptor = open("/etc/nixos/vpn/ocserv.nix", "rt")
    readWriteFileDescriptor = open("/etc/nixos/vpn/ocserv.nix", "wt")

    for line in readOnlyFileDescriptor:
        readWriteFileDescriptor.write(line.replace("enable = false;", "enable = true;"))

    readWriteFileDescriptor.close()
    readOnlyFileDescriptor.close()

    return jsonify(
        status=0
    )

@app.route("/services/ssh/key/send", methods=["PUT"])

def readKey():

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
            fileContent.append(index, "\n      \"" + publicKey + "\"")
            print("done")
            break

    print("[INFO] Writing data from memory to file...", sep="")
    readWriteFileDescriptor = open("/etc/nixos/configuration.nix", "w")
    print("done")
    operationResult = readWriteFileDescriptor.writelines(fileContent)


    return jsonify(
        result=0,
        descriptor = operationResult
    )

if __name__ == '__main__':
    app.run(port=5050, debug=False)