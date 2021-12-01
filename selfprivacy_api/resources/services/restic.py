#!/usr/bin/env python3
"""Backups management module"""
import json
import subprocess
from flask import request
from flask_restful import Resource, reqparse

from selfprivacy_api.resources.services import api
from selfprivacy_api.utils import WriteUserData


class ListAllBackups(Resource):
    """List all restic backups"""

    def get(self):
        """
        Get all restic backups
        ---
        tags:
            - Backups
        security:
            - bearerAuth: []
        responses:
            200:
                description: A list of snapshots
            400:
                description: Bad request
            401:
                description: Unauthorized
        """
        repository_name = request.headers.get("X-Repository-Name")

        backup_listing_command = [
            "restic",
            "-r",
            f"rclone:backblaze:{repository_name}:/sfbackup",
            "snapshots",
            "--json",
        ]

        with subprocess.Popen(
            backup_listing_command,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        ) as backup_listing_process_descriptor:
            snapshots_list = backup_listing_process_descriptor.communicate()[0]

        return snapshots_list.decode("utf-8")


class AsyncCreateBackup(Resource):
    """Create a new restic backup"""

    def put(self):
        """
        Initiate a new restic backup
        ---
        tags:
            - Backups
        security:
            - bearerAuth: []
        responses:
            200:
                description: Backup creation has started
            400:
                description: Bad request
            401:
                description: Unauthorized
        """
        repository_name = request.headers.get("X-Repository-Name")

        backup_command = [
            "restic",
            "-r",
            f"rclone:backblaze:{repository_name}:/sfbackup",
            "--verbose",
            "--json",
            "backup",
            "/var",
        ]

        with open("/tmp/backup.log", "w", encoding="utf-8") as log_file:
            subprocess.Popen(
                backup_command, shell=False, stdout=log_file, stderr=subprocess.STDOUT
            )

        return {
            "status": 0,
            "message": "Backup creation has started",
        }


class CheckBackupStatus(Resource):
    """Check current backup status"""

    def get(self):
        """
        Get backup status
        ---
        tags:
            - Backups
        security:
            - bearerAuth: []
        responses:
            200:
                description: Backup status
            400:
                description: Bad request
            401:
                description: Unauthorized
        """
        backup_status_check_command = ["tail", "-1", "/tmp/backup.log"]

        with subprocess.Popen(
            backup_status_check_command,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        ) as backup_status_check_process_descriptor:
            backup_process_status = (
                backup_status_check_process_descriptor.communicate()[0].decode("utf-8")
            )

        try:
            json.loads(backup_process_status)
        except ValueError:
            return {"message": backup_process_status}
        return backup_process_status


class AsyncRestoreBackup(Resource):
    """Trigger backup restoration process"""

    def put(self):
        """
        Start backup restoration
        ---
        tags:
            - Backups
        security:
            - bearerAuth: []
        responses:
            200:
                description: Backup restoration process started
            400:
                description: Bad request
            401:
                description: Unauthorized
        """
        backup_restoration_command = [
            "restic",
            "-r",
            "rclone:backblaze:sfbackup",
            "var",
            "--json",
        ]

        with open(
            "/tmp/backup.log", "w", encoding="utf-8"
        ) as backup_log_file_descriptor:
            with subprocess.Popen(
                backup_restoration_command,
                shell=False,
                stdout=subprocess.PIPE,
                stderr=backup_log_file_descriptor,
            ) as backup_restoration_process_descriptor:
                backup_restoration_status = "Backup restoration procedure started"

            return {"status": 0, "message": backup_restoration_status}


class BackblazeConfig(Resource):
    """Backblaze config"""

    def put(self):
        """
        Set the new key for backblaze
        ---
        tags:
            - Backups
        security:
            - bearerAuth: []
        parameters:
            - in: body
              required: true
              name: backblazeSettings
              description: New Backblaze settings
              schema:
                type: object
                required:
                    - accountId
                    - accountKey
                    - bucket
                properties:
                    accountId:
                        type: string
                    accountKey:
                        type: string
                    bucket:
                        type: string
        responses:
            200:
                description: New Backblaze settings
            400:
                description: Bad request
            401:
                description: Unauthorized
        """
        parser = reqparse.RequestParser()
        parser.add_argument("accountId", type=str, required=True)
        parser.add_argument("accountKey", type=str, required=True)
        parser.add_argument("bucket", type=str, required=True)
        args = parser.parse_args()

        with WriteUserData() as data:
            data["backblaze"]["accountId"] = args["accountId"]
            data["backblaze"]["accountKey"] = args["accountKey"]
            data["backblaze"]["bucket"] = args["bucket"]

        return "New Backblaze settings saved"


api.add_resource(ListAllBackups, "/restic/backup/list")
api.add_resource(AsyncCreateBackup, "/restic/backup/create")
api.add_resource(CheckBackupStatus, "/restic/backup/status")
api.add_resource(AsyncRestoreBackup, "/restic/backup/restore")
api.add_resource(BackblazeConfig, "/restic/backblaze/config")
