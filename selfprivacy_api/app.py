#!/usr/bin/env python3
from flask import Flask, request, jsonify
from flask_restful import Api
import os

from selfprivacy_api.resources.users import Users
from selfprivacy_api.resources.common import DecryptDisk


def create_app():
    app = Flask(__name__)
    api = Api(app)

    app.config['AUTH_TOKEN'] = os.environ.get('AUTH_TOKEN')

    # Check bearer token
    @app.before_request
    def check_auth():
        auth = request.headers.get("Authorization")
        if auth is None:
            return jsonify({"error": "Missing Authorization header"}), 401

        # Check if token is valid
        if auth != "Bearer " + app.config['AUTH_TOKEN']:
            return jsonify({"error": "Invalid token"}), 401
    
    api.add_resource(Users, "/users")
    api.add_resource(DecryptDisk, "/decryptDisk")
    from selfprivacy_api.resources.system import api_system
    from selfprivacy_api.resources.services import services as api_services

    app.register_blueprint(api_system)
    app.register_blueprint(api_services)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(port=5050, debug=False)
