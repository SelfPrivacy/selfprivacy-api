#!/usr/bin/env python3
"""Backups management module"""
import json
import os
import subprocess
from flask import current_app
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
        bucket = current_app.config["B2_BUCKET"]
        backup_listing_command = [
            "restic",
            "-r",
            f"rclone:backblaze:{bucket}/sfbackup",
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

        try:
            json.loads(snapshots_list.decode("utf-8"))
        except ValueError:
            return {"error": snapshots_list.decode("utf-8")}, 500
        return json.loads(snapshots_list.decode("utf-8"))


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
        bucket = current_app.config["B2_BUCKET"]

        init_command = [
            "restic",
            "-r",
            f"rclone:backblaze:{bucket}/sfbackup",
            "init",
        ]

        backup_command = [
            "restic",
            "-r",
            f"rclone:backblaze:{bucket}/sfbackup",
            "--verbose",
            "--json",
            "backup",
            "/var",
        ]

        subprocess.call(init_command)

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

        # If the log file does not exists
        if os.path.exists("/tmp/backup.log") is False:
            return {"message_type": "not_started", "message": "Backup not started"}

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
            return {"message_type": "error", "message": backup_process_status}
        return json.loads(backup_process_status)


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
        parameters:
            - in: body
              required: true
              name: backup
              description: Backup to restore
              schema:
                type: object
                required:
                    - backupId
                properties:
                    backupId:
                        type: string
        responses:
            200:
                description: Backup restoration process started
            400:
                description: Bad request
            401:
                description: Unauthorized
        """
        parser = reqparse.RequestParser()
        parser.add_argument("backupId", type=str, required=True)
        args = parser.parse_args()
        bucket = current_app.config["B2_BUCKET"]
        backup_id = args["backupId"]

        backup_restoration_command = [
            "restic",
            "-r",
            f"rclone:backblaze:{bucket}/sfbackup",
            "restore",
            backup_id,
            "--target",
            "/var",
            "--json",
        ]

        with open("/tmp/backup.log", "w", encoding="utf-8") as log_file:
            subprocess.Popen(
                backup_restoration_command,
                shell=False,
                stdout=log_file,
                stderr=subprocess.STDOUT,
            )

        return {"status": 0, "message": "Backup restoration procedure started"}


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
