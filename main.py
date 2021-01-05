#!/usr/bin/env python3
from flask import Flask, jsonify, request
from flask_restful import Resource, Api, reqparse
import base64
import pandas as pd
import ast
import subprocess
import os
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
    print(dkim)
    return jsonify(dkim)
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
@app.route("/createUser", methods=["GET"])
def createUser():
    user = subprocess.Popen(["useradd","-m",request.headers.get("X-User")])
    user.communicate()[0]
    return jsonify(user.returncode)
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
if __name__ == '__main__':
    app.run(port=5050, debug=False)
