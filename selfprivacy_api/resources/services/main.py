#!/usr/bin/env python3
"""Services status module"""
import subprocess
from flask_restful import Resource

from . import api


class ServiceStatus(Resource):
    """Get service status"""

    def get(self):
        """
        Get service status
        ---
        tags:
            - Services
        responses:
            200:
                description: Service status
                schema:
                    type: object
                    properties:
                        imap:
                            type: integer
                            description: Dovecot service status
                        smtp:
                            type: integer
                            description: Postfix service status
                        http:
                            type: integer
                            description: Nginx service status
                        bitwarden:
                            type: integer
                            description: Bitwarden service status
                        gitea:
                            type: integer
                            description: Gitea service status
                        nextcloud:
                            type: integer
                            description: Nextcloud service status
                        ocserv:
                            type: integer
                            description: OpenConnect VPN service status
                        pleroma:
                            type: integer
                            description: Pleroma service status
            401:
                description: Unauthorized
        """
        imap_service = subprocess.Popen(["systemctl", "status", "dovecot2.service"])
        imap_service.communicate()[0]
        smtp_service = subprocess.Popen(["systemctl", "status", "postfix.service"])
        smtp_service.communicate()[0]
        http_service = subprocess.Popen(["systemctl", "status", "nginx.service"])
        http_service.communicate()[0]
        bitwarden_service = subprocess.Popen(
            ["systemctl", "status", "bitwarden_rs.service"]
        )
        bitwarden_service.communicate()[0]
        gitea_service = subprocess.Popen(["systemctl", "status", "gitea.service"])
        gitea_service.communicate()[0]
        nextcloud_service = subprocess.Popen(
            ["systemctl", "status", "phpfpm-nextcloud.service"]
        )
        nextcloud_service.communicate()[0]
        ocserv_service = subprocess.Popen(["systemctl", "status", "ocserv.service"])
        ocserv_service.communicate()[0]
        pleroma_service = subprocess.Popen(["systemctl", "status", "pleroma.service"])
        pleroma_service.communicate()[0]

        return {
            "imap": imap_service.returncode,
            "smtp": smtp_service.returncode,
            "http": http_service.returncode,
            "bitwarden": bitwarden_service.returncode,
            "gitea": gitea_service.returncode,
            "nextcloud": nextcloud_service.returncode,
            "ocserv": ocserv_service.returncode,
            "pleroma": pleroma_service.returncode,
        }


api.add_resource(ServiceStatus, "/status")
