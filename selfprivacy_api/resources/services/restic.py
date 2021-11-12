#!/usr/bin/env python3
from flask import request
from flask_restful import Resource
import subprocess

from selfprivacy_api.resources.services import api

# List all restic backups
class ListAllBackups(Resource):
    def get(self):
        backupListingCommand = """
            restic -r b2:{0}:/sfbackup snapshots --password-file /var/lib/restic/rpass --json
        """.format(
            request.headers.get("X-Repository-Name")
        )

        backupListingProcessDescriptor = subprocess.Popen(
            backupListingCommand,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

        snapshotsList = backupListingProcessDescriptor.communicate()[0]

        return snapshotsList.decode("utf-8")


# Create a new restic backup
class CreateBackup(Resource):
    def put(self):
        backupCommand = """
            restic -r b2:{0}:/sfbackup --verbose backup /var --password-file /var/lib/restic/rpass
        """.format(
            request.headers.get("X-Repository-Name")
        )

        backupProcessDescriptor = subprocess.Popen(
            backupCommand, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )

        commandOutput = backupProcessDescriptor.communicate()[0]

        return {
            "status": 0,
            "message": "Backup creation has started",
        }


api.add_resource(ListAllBackups, "/restic/backup/list")
api.add_resource(CreateBackup, "/restic/backup/create")
