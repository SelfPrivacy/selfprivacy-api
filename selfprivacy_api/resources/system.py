#!/usr/bin/env python3
"""System management module"""
import os
import subprocess
import pytz
from flask import Blueprint
from flask_restful import Resource, Api, reqparse
from selfprivacy_api.graphql.queries.system import (
    get_python_version,
    get_system_version,
)

from selfprivacy_api.utils import WriteUserData, ReadUserData

api_system = Blueprint("system", __name__, url_prefix="/system")
api = Api(api_system)


class Timezone(Resource):
    """Change timezone of NixOS"""

    def get(self):
        """
        Get current system timezone
        ---
        tags:
            - System
        security:
            - bearerAuth: []
        responses:
            200:
                description: Timezone
            400:
                description: Bad request
        """
        with ReadUserData() as data:
            if "timezone" not in data:
                return "Europe/Uzhgorod"
            return data["timezone"]

    def put(self):
        """
        Change system timezone
        ---
        tags:
            - System
        security:
            - bearerAuth: []
        parameters:
            - name: timezone
              in: body
              required: true
              description: Timezone to set
              schema:
                type: object
                required:
                    - timezone
                properties:
                    timezone:
                        type: string
        responses:
            200:
                description: Timezone changed
            400:
                description: Bad request
        """
        parser = reqparse.RequestParser()
        parser.add_argument("timezone", type=str, required=True)
        timezone = parser.parse_args()["timezone"]

        # Check if timezone is a valid tzdata string
        if timezone not in pytz.all_timezones:
            return {"error": "Invalid timezone"}, 400

        with WriteUserData() as data:
            data["timezone"] = timezone
        return "Timezone changed"


class AutoUpgrade(Resource):
    """Enable/disable automatic upgrades and reboots"""

    def get(self):
        """
        Get current system autoupgrade settings
        ---
        tags:
            - System
        security:
            - bearerAuth: []
        responses:
            200:
                description: Auto-upgrade settings
            400:
                description: Bad request
        """
        with ReadUserData() as data:
            if "autoUpgrade" not in data:
                return {"enable": True, "allowReboot": False}
            if "enable" not in data["autoUpgrade"]:
                data["autoUpgrade"]["enable"] = True
            if "allowReboot" not in data["autoUpgrade"]:
                data["autoUpgrade"]["allowReboot"] = False
            return data["autoUpgrade"]

    def put(self):
        """
        Change system auto upgrade settings
        ---
        tags:
            - System
        security:
            - bearerAuth: []
        parameters:
            - name: autoUpgrade
              in: body
              required: true
              description: Auto upgrade settings
              schema:
                type: object
                required:
                    - enable
                    - allowReboot
                properties:
                    enable:
                        type: boolean
                    allowReboot:
                        type: boolean
        responses:
            200:
                description: New settings saved
            400:
                description: Bad request
        """
        parser = reqparse.RequestParser()
        parser.add_argument("enable", type=bool, required=False)
        parser.add_argument("allowReboot", type=bool, required=False)
        args = parser.parse_args()
        enable = args["enable"]
        allow_reboot = args["allowReboot"]

        with WriteUserData() as data:
            if "autoUpgrade" not in data:
                data["autoUpgrade"] = {}
            if enable is not None:
                data["autoUpgrade"]["enable"] = enable
            if allow_reboot is not None:
                data["autoUpgrade"]["allowReboot"] = allow_reboot
        return "Auto-upgrade settings changed"


class RebuildSystem(Resource):
    """Rebuild NixOS"""

    def get(self):
        """
        Rebuild NixOS with nixos-rebuild switch
        ---
        tags:
            - System
        security:
            - bearerAuth: []
        responses:
            200:
                description: System rebuild has started
            401:
                description: Unauthorized
        """
        rebuild_result = subprocess.Popen(
            ["systemctl", "start", "sp-nixos-rebuild.service"], start_new_session=True
        )
        rebuild_result.communicate()[0]
        return rebuild_result.returncode


class RollbackSystem(Resource):
    """Rollback NixOS"""

    def get(self):
        """
        Rollback NixOS with nixos-rebuild switch --rollback
        ---
        tags:
            - System
        security:
            - bearerAuth: []
        responses:
            200:
                description: System rollback has started
            401:
                description: Unauthorized
        """
        rollback_result = subprocess.Popen(
            ["systemctl", "start", "sp-nixos-rollback.service"], start_new_session=True
        )
        rollback_result.communicate()[0]
        return rollback_result.returncode


class UpgradeSystem(Resource):
    """Upgrade NixOS"""

    def get(self):
        """
        Upgrade NixOS with nixos-rebuild switch --upgrade
        ---
        tags:
            - System
        security:
            - bearerAuth: []
        responses:
            200:
                description: System upgrade has started
            401:
                description: Unauthorized
        """
        upgrade_result = subprocess.Popen(
            ["systemctl", "start", "sp-nixos-upgrade.service"], start_new_session=True
        )
        upgrade_result.communicate()[0]
        return upgrade_result.returncode


class RebootSystem(Resource):
    """Reboot the system"""

    def get(self):
        """
        Reboot the system
        ---
        tags:
            - System
        security:
            - bearerAuth: []
        responses:
            200:
                description: System reboot has started
            401:
                description: Unauthorized
        """
        subprocess.Popen(["reboot"], start_new_session=True)
        return "System reboot has started"


class SystemVersion(Resource):
    """Get system version from uname"""

    def get(self):
        """
        Get system version from uname -a
        ---
        tags:
            - System
        security:
            - bearerAuth: []
        responses:
            200:
                description: OK
            401:
                description: Unauthorized
        """
        return {
            "system_version": get_system_version(),
        }


class PythonVersion(Resource):
    """Get python version"""

    def get(self):
        """
        Get python version used by this API
        ---
        tags:
            - System
        security:
            - bearerAuth: []
        responses:
            200:
                description: OK
            401:
                description: Unauthorized
        """
        return get_python_version()


class PullRepositoryChanges(Resource):
    """Pull NixOS config repository changes"""

    def get(self):
        """
        Pull Repository Changes
        ---
        tags:
            - System
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
            shell=False,
        )

        data = git_pull_process_descriptor.communicate()[0].decode("utf-8")

        os.chdir(current_working_directory)

        if git_pull_process_descriptor.returncode == 0:
            return {
                "status": 0,
                "message": "Update completed successfully",
                "data": data,
            }
        return {
            "status": git_pull_process_descriptor.returncode,
            "message": "Something went wrong",
            "data": data,
        }, 500


api.add_resource(Timezone, "/configuration/timezone")
api.add_resource(AutoUpgrade, "/configuration/autoUpgrade")
api.add_resource(RebuildSystem, "/configuration/apply")
api.add_resource(RollbackSystem, "/configuration/rollback")
api.add_resource(UpgradeSystem, "/configuration/upgrade")
api.add_resource(RebootSystem, "/reboot")
api.add_resource(SystemVersion, "/version")
api.add_resource(PythonVersion, "/pythonVersion")
api.add_resource(PullRepositoryChanges, "/configuration/pull")
