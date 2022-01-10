#!/usr/bin/env python3
"""Backups management module"""
from flask_restful import Resource, reqparse

from selfprivacy_api.resources.services import api
from selfprivacy_api.utils import WriteUserData
from selfprivacy_api.restic_controller import tasks as restic_tasks
from selfprivacy_api.restic_controller import ResticController, ResticStates


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

        restic = ResticController()
        return restic.snapshot_list


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
            409:
                description: Backup already in progress
        """
        restic = ResticController()
        if restic.state is ResticStates.NO_KEY:
            return {"error": "No key provided"}, 400
        if restic.state is ResticStates.INITIALIZING:
            return {"error": "Backup is initializing"}, 400
        if restic.state is ResticStates.BACKING_UP:
            return {"error": "Backup is already running"}, 409
        restic_tasks.start_backup()
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
        restic = ResticController()

        return {
            "status": restic.state.name,
            "progress": restic.progress,
            "error_message": restic.error_message,
        }


class ForceReloadSnapshots(Resource):
    """Force reload snapshots"""

    def get(self):
        """
        Force reload snapshots
        ---
        tags:
            - Backups
        security:
            - bearerAuth: []
        responses:
            200:
                description: Snapshots reloaded
            400:
                description: Bad request
            401:
                description: Unauthorized
        """
        restic_tasks.load_snapshots()
        return {
            "status": 0,
            "message": "Snapshots reload started",
        }


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

        restic = ResticController()
        if restic.state is ResticStates.NO_KEY:
            return {"error": "No key provided"}, 400
        if restic.state is ResticStates.NOT_INITIALIZED:
            return {"error": "Repository is not initialized"}, 400
        if restic.state is ResticStates.BACKING_UP:
            return {"error": "Backup is already running"}, 409
        if restic.state is ResticStates.INITIALIZING:
            return {"error": "Repository is initializing"}, 400
        if restic.state is ResticStates.RESTORING:
            return {"error": "Restore is already running"}, 409
        for backup in restic.snapshot_list:
            if backup["short_id"] == args["backupId"]:
                restic_tasks.restore_from_backup(args["backupId"])
                return {
                    "status": 0,
                    "message": "Backup restoration procedure started",
                }

        return {"error": "Backup not found"}, 404


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
            if "backblaze" not in data:
                data["backblaze"] = {}
            data["backblaze"]["accountId"] = args["accountId"]
            data["backblaze"]["accountKey"] = args["accountKey"]
            data["backblaze"]["bucket"] = args["bucket"]

        restic_tasks.update_keys_from_userdata()

        return "New Backblaze settings saved"


api.add_resource(ListAllBackups, "/restic/backup/list")
api.add_resource(AsyncCreateBackup, "/restic/backup/create")
api.add_resource(CheckBackupStatus, "/restic/backup/status")
api.add_resource(AsyncRestoreBackup, "/restic/backup/restore")
api.add_resource(BackblazeConfig, "/restic/backblaze/config")
api.add_resource(ForceReloadSnapshots, "/restic/backup/reload")
