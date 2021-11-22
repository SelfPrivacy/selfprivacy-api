#!/usr/bin/env python3
"""SelfPrivacy server management API"""
import os
from flask import Flask, request, jsonify
from flask_restful import Api
from flask_swagger import swagger
from flask_swagger_ui import get_swaggerui_blueprint

from selfprivacy_api.resources.users import User, Users
from selfprivacy_api.resources.common import ApiVersion, DecryptDisk
from selfprivacy_api.resources.system import api_system
from selfprivacy_api.resources.services import services as api_services

swagger_blueprint = get_swaggerui_blueprint(
    "/api/docs", "/api/swagger.json", config={"app_name": "SelfPrivacy API"}
)


def create_app():
    """Initiate Flask app and bind routes"""
    app = Flask(__name__)
    api = Api(app)

    app.config["AUTH_TOKEN"] = os.environ.get("AUTH_TOKEN")
    if app.config["AUTH_TOKEN"] is None:
        raise ValueError("AUTH_TOKEN is not set")
    app.config["ENABLE_SWAGGER"] = os.environ.get("ENABLE_SWAGGER", "0")

    # Check bearer token
    @app.before_request
    def check_auth():
        # Exclude swagger-ui
        if not request.path.startswith("/api"):
            auth = request.headers.get("Authorization")
            if auth is None:
                return jsonify({"error": "Missing Authorization header"}), 401

            # Check if token is valid
            if auth != "Bearer " + app.config["AUTH_TOKEN"]:
                return jsonify({"error": "Invalid token"}), 401

    api.add_resource(ApiVersion, "/api/version")
    api.add_resource(Users, "/users")
    api.add_resource(User, "/users/<string:username>")
    api.add_resource(DecryptDisk, "/decryptDisk")

    app.register_blueprint(api_system)
    app.register_blueprint(api_services)

    @app.route("/api/swagger.json")
    def spec():
        if app.config["ENABLE_SWAGGER"] == "1":
            swag = swagger(app)
            swag["info"]["version"] = "1.1.0"
            swag["info"]["title"] = "SelfPrivacy API"
            swag["info"]["description"] = "SelfPrivacy API"
            swag["securityDefinitions"] = {
                "bearerAuth": {
                    "type": "apiKey",
                    "name": "Authorization",
                    "in": "header",
                }
            }
            swag["security"] = [{"bearerAuth": []}]

            return jsonify(swag)
        return jsonify({}), 404

    if app.config["ENABLE_SWAGGER"] == "1":
        app.register_blueprint(swagger_blueprint, url_prefix="/api/docs")

    return app


if __name__ == "__main__":
    created_app = create_app()
    created_app.run(port=5050, debug=False)
