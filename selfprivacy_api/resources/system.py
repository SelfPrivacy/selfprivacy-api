#!/usr/bin/env python3
from flask import Blueprint
from flask_restful import Resource, Api
import subprocess

api_system = Blueprint("system", __name__, url_prefix="/system")
api = Api(api_system)

# Rebuild NixOS
class RebuildSystem(Resource):
    def get(self):
        rebuildResult = subprocess.Popen(["nixos-rebuild", "switch"])
        rebuildResult.communicate()[0]
        return rebuildResult.returncode


# Rollback NixOS
class RollbackSystem(Resource):
    def get(self):
        rollbackResult = subprocess.Popen(["nixos-rebuild", "switch", "--rollback"])
        rollbackResult.communicate()[0]
        return rollbackResult.returncode


# Upgrade NixOS
class UpgradeSystem(Resource):
    def get(self):
        upgradeResult = subprocess.Popen(["nixos-rebuild", "switch", "--upgrade"])
        upgradeResult.communicate()[0]
        return upgradeResult.returncode


# Get system version from uname
class SystemVersion(Resource):
    def get(self):
        return {
            "system_version": subprocess.check_output(["uname", "-a"])
            .decode("utf-8")
            .strip()
        }


# Get python version
class PythonVersion(Resource):
    def get(self):
        return subprocess.check_output(["python", "-V"]).decode("utf-8").strip()


api.add_resource(RebuildSystem, "/configuration/apply")
api.add_resource(RollbackSystem, "/configuration/rollback")
api.add_resource(UpgradeSystem, "/upgrade")
api.add_resource(SystemVersion, "/version")
api.add_resource(PythonVersion, "/pythonVersion")
