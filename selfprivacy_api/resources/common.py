#!/usr/bin/env python3
"""Unassigned views"""
from flask_restful import Resource


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
        return {"version": "1.2.1"}
