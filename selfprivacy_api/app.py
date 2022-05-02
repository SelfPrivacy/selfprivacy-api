#!/usr/bin/env python3
"""SelfPrivacy server management API"""
import os
from gevent import monkey


from flask import Flask, request, jsonify
from flask_restful import Api
from flask_swagger import swagger
from flask_swagger_ui import get_swaggerui_blueprint

from selfprivacy_api.resources.users import User, Users
from selfprivacy_api.resources.common import ApiVersion
from selfprivacy_api.resources.system import api_system
from selfprivacy_api.resources.services import services as api_services
from selfprivacy_api.resources.api_auth import auth as api_auth

from selfprivacy_api.restic_controller.tasks import huey, init_restic

from selfprivacy_api.migrations import run_migrations

from selfprivacy_api.utils.auth import is_token_valid

swagger_blueprint = get_swaggerui_blueprint(
    "/api/docs", "/api/swagger.json", config={"app_name": "SelfPrivacy API"}
)


def create_app(test_config=None):
    """Initiate Flask app and bind routes"""
    app = Flask(__name__)
    api = Api(app)

    if test_config is None:
        app.config["ENABLE_SWAGGER"] = os.environ.get("ENABLE_SWAGGER", "0")
        app.config["B2_BUCKET"] = os.environ.get("B2_BUCKET")
    else:
        app.config.update(test_config)

    # Check bearer token
    @app.before_request
    def check_auth():
        # Exclude swagger-ui, /auth/new_device/authorize, /auth/recovery_token/use
        if request.path.startswith("/api"):
            pass
        elif request.path.startswith("/auth/new_device/authorize"):
            pass
        elif request.path.startswith("/auth/recovery_token/use"):
            pass
        else:
            auth = request.headers.get("Authorization")
            if auth is None:
                return jsonify({"error": "Missing Authorization header"}), 401
            # Strip Bearer from auth header
            auth = auth.replace("Bearer ", "")
            if not is_token_valid(auth):
                return jsonify({"error": "Invalid token"}), 401

    api.add_resource(ApiVersion, "/api/version")
    api.add_resource(Users, "/users")
    api.add_resource(User, "/users/<string:username>")

    app.register_blueprint(api_system)
    app.register_blueprint(api_services)
    app.register_blueprint(api_auth)

    @app.route("/api/swagger.json")
    def spec():
        if app.config["ENABLE_SWAGGER"] == "1":
            swag = swagger(app)
            swag["info"]["version"] = "1.2.4"
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
    monkey.patch_all()
    created_app = create_app()
    run_migrations()
    huey.start()
    init_restic()
    created_app.run(port=5050, debug=False)
