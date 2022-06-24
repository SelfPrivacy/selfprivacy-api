#!/usr/bin/env python3
"""Unassigned views"""
from flask_restful import Resource
from selfprivacy_api.resolvers.api import get_api_version

class ApiVersion(Resource):
    """SelfPrivacy API version"""

    def get(self):
        """Get API version
        ---
        tags:
            - System
        responses:
            200:
                description: API version
                schema:
                    type: object
                    properties:
                        version:
                            type: string
                            description: API version
            401:
                description: Unauthorized
        """
        return {"version": get_api_version()}
