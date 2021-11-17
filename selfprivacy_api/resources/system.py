#!/usr/bin/env python3
"""System management module"""
import subprocess
from flask import Blueprint
from flask_restful import Resource, Api

api_system = Blueprint("system", __name__, url_prefix="/system")
api = Api(api_system)


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
        rebuild_result = subprocess.Popen(["nixos-rebuild", "switch"])
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
        rollback_result = subprocess.Popen(["nixos-rebuild", "switch", "--rollback"])
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
        upgrade_result = subprocess.Popen(["nixos-rebuild", "switch", "--upgrade"])
        upgrade_result.communicate()[0]
        return upgrade_result.returncode


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
            "system_version": subprocess.check_output(["uname", "-a"])
            .decode("utf-8")
            .strip()
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
        return subprocess.check_output(["python", "-V"]).decode("utf-8").strip()


api.add_resource(RebuildSystem, "/configuration/apply")
api.add_resource(RollbackSystem, "/configuration/rollback")
api.add_resource(UpgradeSystem, "/configuration/upgrade")
api.add_resource(SystemVersion, "/version")
api.add_resource(PythonVersion, "/pythonVersion")
