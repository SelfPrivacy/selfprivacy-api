#!/usr/bin/env python3
"""Services management module"""
from flask import Blueprint
from flask_restful import Api

from . import (
    bitwarden,
    gitea,
    mailserver,
    main,
    nextcloud,
    ocserv,
    pleroma,
    restic,
    ssh,
)

services = Blueprint("services", __name__, url_prefix="/services")
api = Api(services)
