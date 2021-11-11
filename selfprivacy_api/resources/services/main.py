#!/usr/bin/env python3
from flask_restful import Resource, Api
import subprocess

from . import api

# Get service status
class ServiceStatus(Resource):
    def get(self):
        imapService = subprocess.Popen(["systemctl", "status", "dovecot2.service"])
        imapService.communicate()[0]
        smtpService = subprocess.Popen(["systemctl", "status", "postfix.service"])
        smtpService.communicate()[0]
        httpService = subprocess.Popen(["systemctl", "status", "nginx.service"])
        httpService.communicate()[0]
        bitwardenService = subprocess.Popen(
            ["systemctl", "status", "bitwarden_rs.service"]
        )
        bitwardenService.communicate()[0]
        giteaService = subprocess.Popen(["systemctl", "status", "gitea.service"])
        giteaService.communicate()[0]
        nextcloudService = subprocess.Popen(
            ["systemctl", "status", "phpfpm-nextcloud.service"]
        )
        nextcloudService.communicate()[0]
        ocservService = subprocess.Popen(["systemctl", "status", "ocserv.service"])
        ocservService.communicate()[0]
        pleromaService = subprocess.Popen(["systemctl", "status", "pleroma.service"])
        pleromaService.communicate()[0]

        return {
            "imap": imapService.returncode,
            "smtp": smtpService.returncode,
            "http": httpService.returncode,
            "bitwarden": bitwardenService.returncode,
            "gitea": giteaService.returncode,
            "nextcloud": nextcloudService.returncode,
            "ocserv": ocservService.returncode,
            "pleroma": pleromaService.returncode,
        }


api.add_resource(ServiceStatus, "/status")
