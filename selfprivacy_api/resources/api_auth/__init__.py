#!/usr/bin/env python3
"""API authentication module"""

from flask import Blueprint
from flask_restful import Api

auth = Blueprint("auth", __name__, url_prefix="/auth")
api = Api(auth)

from . import (
    new_device,
    recovery_token,
    app_tokens,
)
