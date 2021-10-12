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


@app.route("/system/configuration/apply", methods=["GET"])
def rebuildSystem():
     rebuildResult = subprocess.Popen(["nixos-rebuild","switch"])
     rebuildResult.communicate()[0]
     return jsonify(
         status=rebuildResult.returncode
         )


@app.route("/system/configuration/rollback", methods=["GET"])
def rollbackSystem():
     rollbackResult = subprocess.Popen(["nixos-rebuild","switch","--rollback"])
     rollbackResult.communicate()[0]
     return jsonify(rollbackResult.returncode)


@app.route("/system/upgrade", methods=["GET"])
def upgradeSystem():
     upgradeResult = subprocess.Popen(["nixos-rebuild","switch","--upgrade"])
     upgradeResult.communicate()[0]
     return jsonify(
         status=upgradeResult.returncode
         )


@app.route("/users/create", methods=["POST"])
def createUser():

    rawPassword = request.headers.get("X-Password")
    hashingCommand = '''
        mkpasswd -m sha-512 {0}
    '''.format(rawPassword)
    passwordHashProcessDescriptor = subprocess.Popen([hashingCommand, stdout=subprocess.PIPE, stderr=STDOUT)
    hashedPassword = passwordHashProcessDescriptor.communicate()[0]
    hashedPassword = hashedPassword.decode("ascii")

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
      """.format(request.headers.get("X-User"), request.headers.get("X-Password"))

    mailUserTemplate = """
        \"{0}@{2}\" = {
          hashedPassword = 
            \"{1}\";
          catchAll = [ \"{2}\" ];

          sieveScript = ''
          require [\"fileinto\", \"mailbox\"];
          if header :contains \"Chat-Version\" \"1.0\"
          {     
            fileinto :create \"DeltaChat\";
                stop;
          }
        '';
        };
    """.format(request.headers.get("X-User"), request.headers.get("X-Password"), request.headers.get("X-Domain"))

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
    userConfigurationWriteOperationResult = readWriteFileDescriptor.writelines(fileContent)
    print("done")

    readOnlyFileDescriptor.close()
    readWriteFileDescriptor.close()

    print("[INFO] Opening /etc/nixos/mailserver/system/mailserver.nix.nix for reading...", sep="")
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
            print("[INFO] Writing new user configuration snippet to memory...", sep="")
            fileContent.insert(index+1, mailUserTemplate)
            print("done")
            break
        index += 1

    readWriteFileDescriptor = open("/etc/nixos/mailserver/system/mailserver.nix", "w")

    mailUserConfigurationWriteOperationResult = readWriteFileDescriptor.writelines(fileContent)

    return jsonify(
        result=0,
        descriptor0 = userConfigurationWriteOperationResult,
        descriptor1 = mailUserConfigurationWriteOperationResult
    )


@app.route("/deleteUser", methods=["DELETE"])
def deleteUser():
    user = subprocess.Popen(["userdel",request.headers.get("X-User")])
    user.communicate()[0]
    return jsonify(user.returncode)


@app.route("/services/status", methods=["GET"])

def getServiceStatus():
    imapService = subprocess.Popen(["systemctl", "status", "dovecot2.service"])
    imapService.communicate()[0]
    smtpService = subprocess.Popen(["systemctl", "status", "postfix.service"])
    smtpService.communicate()[0]
    httpService = subprocess.Popen(["systemctl", "status", "nginx.service"])
    httpService.communicate()[0]
    bitwardenService = subprocess.Popen(["systemctl", "status", "bitwarden_rs.service"])
    bitwardenService.communicate()[0]
    giteaService = subprocess.Popen(["systemctl", "status", "gitea.service"])
    giteaService.communicate()[0]
    nextcloudService = subprocess.Popen(["systemctl", "status", "phpfpm-nextcloud.service"])
    nextcloudService.communicate()[0]
    ocservService = subprocess.Popen(["systemctl", "status", "ocserv.service"])
    ocservService.communicate()[0]
    pleromaService = subprocess.Popen(["systemctl", "status", "pleroma.service"])
    pleromaService.communicate()[0]

    return jsonify(
        imap=imapService.returncode,
        smtp=smtpService.returncode,
        http=httpService.returncode,
        bitwarden=bitwardenService.returncode,
        gitea=giteaService.returncode,
        nextcloud=nextcloudService.returncode,
        ocserv=ocservService.returncode,
        pleroma=pleromaService.returncode
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

    fileContent = fileContent.replace("enable = false;", "enable = true;")     
    readOnlyFileDescriptor.close()

    readWriteFileDescriptor = open("/etc/nixos/configuration.nix", "wt") 

    writeOperationDescriptor = readWriteFileDescriptor.write(fileContent)
    readWriteFileDescriptor.close()
    
    return jsonify(
        status=0,
        descriptor=writeOperationDescriptor

    )

# Bitwarden

@app.route("/services/bitwarden/enable", methods=["POST"])

def enableBitwarden():
    readOnlyFileDescriptor = open("/etc/nixos/passmgr/bitwarden.nix", "rt")
    

    fileContent = readOnlyFileDescriptor.read()

    fileContent = fileContent.replace("enable = false;", "enable = true;")     
    readOnlyFileDescriptor.close()

    readWriteFileDescriptor = open("/etc/nixos/passmgr/bitwarden.nix", "wt") 

    writeOperationDescriptor = readWriteFileDescriptor.write(fileContent)
    readWriteFileDescriptor.close()
    
    return jsonify(
        status=0,
        descriptor=writeOperationDescriptor
    )

@app.route("/services/bitwarden/disable", methods=["POST"])

def disableBitwarden():

    readOnlyFileDescriptor = open("/etc/nixos/passmgr/bitwarden.nix", "rt")
    

    fileContent = readOnlyFileDescriptor.read()

    fileContent = fileContent.replace("enable = true;", "enable = false;")     
    readOnlyFileDescriptor.close()

    readWriteFileDescriptor = open("/etc/nixos/passmgr/bitwarden.nix", "wt") 

    writeOperationDescriptor = readWriteFileDescriptor.write(fileContent)
    readWriteFileDescriptor.close()
    
    return jsonify(
        status=0,
        descriptor=writeOperationDescriptor
    )


#Gitea

@app.route("/services/gitea/disable", methods=["POST"])

def disableGitea():
    readOnlyFileDescriptor = open("/etc/nixos/git/gitea.nix", "rt")
    

    fileContent = readOnlyFileDescriptor.read()

    fileContent = fileContent.replace("enable = true;", "enable = false;")     
    readOnlyFileDescriptor.close()

    readWriteFileDescriptor = open("/etc/nixos/git/gitea.nix", "wt") 

    writeOperationDescriptor = readWriteFileDescriptor.write(fileContent)
    readWriteFileDescriptor.close()
    
    return jsonify(
        status=0,
        descriptor=writeOperationDescriptor
    )

@app.route("/services/gitea/enable", methods=["POST"])

def enableGitea():
    readOnlyFileDescriptor = open("/etc/nixos/git/gitea.nix", "rt")
    

    fileContent = readOnlyFileDescriptor.read()

    fileContent = fileContent.replace("enable = false;", "enable = true;")     
    readOnlyFileDescriptor.close()

    readWriteFileDescriptor = open("/etc/nixos/git/gitea.nix", "wt") 

    writeOperationDescriptor = readWriteFileDescriptor.write(fileContent)
    readWriteFileDescriptor.close()
    
    return jsonify(
        status=0,
        descriptor=writeOperationDescriptor
    )

#Nextcloud

@app.route("/services/nextcloud/disable", methods=["POST"])

def disableNextcloud():
    readOnlyFileDescriptor = open("/etc/nixos/nextcloud/nextcloud.nix", "rt")
    

    fileContent = readOnlyFileDescriptor.read()

    fileContent = fileContent.replace("enable = true;", "enable = false;")     
    readOnlyFileDescriptor.close()

    readWriteFileDescriptor = open("/etc/nixos/nextcloud/nextcloud.nix", "wt") 

    writeOperationDescriptor = readWriteFileDescriptor.write(fileContent)
    readWriteFileDescriptor.close()
    
    return jsonify(
        status=0,
        descriptor=writeOperationDescriptor
    )

@app.route("/services/nextcloud/enable", methods=["POST"])

def enableNextcloud():
    readOnlyFileDescriptor = open("/etc/nixos/nextcloud/nextcloud.nix", "rt")
    

    fileContent = readOnlyFileDescriptor.read()

    fileContent = fileContent.replace("enable = false;", "enable = true;")     
    readOnlyFileDescriptor.close()

    readWriteFileDescriptor = open("/etc/nixos/nextcloud/nextcloud.nix", "wt") 

    writeOperationDescriptor = readWriteFileDescriptor.write(fileContent)
    readWriteFileDescriptor.close()
    
    return jsonify(
        status=0,
        descriptor=writeOperationDescriptor
    )

#Pleroma

@app.route("/services/pleroma/disable", methods=["POST"])

def disablePleroma():
    readOnlyFileDescriptor = open("/etc/nixos/social/pleroma.nix", "rt")
    

    fileContent = readOnlyFileDescriptor.read()

    fileContent = fileContent.replace("enable = true;", "enable = false;")     
    readOnlyFileDescriptor.close()

    readWriteFileDescriptor = open("/etc/nixos/social/pleroma.nix", "wt") 

    writeOperationDescriptor = readWriteFileDescriptor.write(fileContent)
    readWriteFileDescriptor.close()
    
    return jsonify(
        status=0,
        descriptor=writeOperationDescriptor
    )

@app.route("/services/pleroma/enable", methods=["POST"])

def enablePleroma():
    readOnlyFileDescriptor = open("/etc/nixos/social/pleroma.nix", "rt")
    

    fileContent = readOnlyFileDescriptor.read()

    fileContent = fileContent.replace("enable = false;", "enable = true;")     
    readOnlyFileDescriptor.close()

    readWriteFileDescriptor = open("/etc/nixos/social/pleroma.nix", "wt") 

    writeOperationDescriptor = readWriteFileDescriptor.write(fileContent)
    readWriteFileDescriptor.close()
    
    return jsonify(
        status=0,
        descriptor=writeOperationDescriptor
    )

#Ocserv

@app.route("/services/ocserv/disable", methods=["POST"])

def disableOcserv():
    readOnlyFileDescriptor = open("/etc/nixos/vpn/ocserv.nix", "rt")
    

    fileContent = readOnlyFileDescriptor.read()

    fileContent = fileContent.replace("enable = true;", "enable = false;")     
    readOnlyFileDescriptor.close()

    readWriteFileDescriptor = open("/etc/nixos/vpn/ocserv.nix", "wt") 

    writeOperationDescriptor = readWriteFileDescriptor.write(fileContent)
    readWriteFileDescriptor.close()
    
    return jsonify(
        status=0,
        descriptor=writeOperationDescriptor
    )

@app.route("/services/ocserv/enable", methods=["POST"])

def enableOcserv():
    readOnlyFileDescriptor = open("/etc/nixos/vpn/ocserv.nix", "rt")
    

    fileContent = readOnlyFileDescriptor.read()

    fileContent = fileContent.replace("enable = true;", "enable = false;")     
    readOnlyFileDescriptor.close()

    readWriteFileDescriptor = open("/etc/nixos/vpn/ocserv.nix", "wt") 

    writeOperationDescriptor = readWriteFileDescriptor.write(fileContent)
    readWriteFileDescriptor.close()
    
    return jsonify(
        status=0,
        descriptor=writeOperationDescriptor
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