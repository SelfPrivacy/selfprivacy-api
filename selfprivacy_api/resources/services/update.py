#!/usr/bin/env/python3
"""Update dispatch module"""
import os
import subprocess
from flask_restful import Resource, reqparse

from selfprivacy_api.resources.services import api


class PullRepositoryChanges(Resource):
    def get(self):
        """
        Pull Repository Changes
        ---
        tags:
            - Update
        security:
            - bearerAuth: []
        responses:
            200:
                description: Got update
            201:
                description: Nothing to update
            401:
                description: Unauthorized
            500:
                description: Something went wrong
        """

        git_pull_command = ["git", "pull"]

        current_working_directory = os.getcwd()
        os.chdir("/etc/nixos")


        git_pull_process_descriptor = subprocess.Popen(
            git_pull_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=False
        )


        git_pull_process_descriptor.communicate()[0]

        os.chdir(current_working_directory)

        if git_pull_process_descriptor.returncode == 0:
            return {
                "status": 0,
                "message": "Update completed successfully"
            }
        elif git_pull_process_descriptor.returncode > 0:
            return {
                "status": git_pull_process_descriptor.returncode,
                "message": "Something went wrong"
            }, 500

api.add_resource(PullRepositoryChanges, "/update")
