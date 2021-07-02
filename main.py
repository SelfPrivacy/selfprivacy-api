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
     return jsonify(rebuildResult.returncode)


@app.route("/rollback", methods=["GET"])
def rollbackSystem():
     rollbackResult = subprocess.Popen(["nixos-rebuild","switch","--rollback"])
     rollbackResult.communicate()[0]
     return jsonify(rollbackResult.returncode)


@app.route("/upgrade", methods=["GET"])
def upgradeSystem():
     upgradeResult = subprocess.Popen(["nixos-rebuild","switch","--upgrade"])
     upgradeResult.communicate()[0]
     return jsonify(upgradeResult.returncode)


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

    print("[TRACE] {0}".format(userTemplate))

    for line in fileContent:
        index -= 1
        if line.startswith("      #begin"):
            print("[DEBUG] Found user configuration snippet match!")
            print("[INFO] Writing new user configuration snippet to memory...", sep="")
            fileContent.insert(index, userTemplate)
            print("done")

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


@app.route("/enableSSH", methods=["POST"])

def enableSSH():
    readOnlyFileDescriptor = open("/etc/nixos/configuration.nix", "rt")
    readWriteFileDescriptor = open("/etc/nixos/configuration.nix", "wt")

    for line in readOnlyFileDescriptor:
        readWriteFileDescriptor.write(line.replace("services.openssh.enable = false;", "services.openssh.enable = true;"))

    readWriteFileDescriptor.close()
    readOnlyFileDescriptor.close()

    return jsonify(
        status=0
    )


if __name__ == '__main__':
    app.run(port=5050, debug=False)