#!/usr/bin/env python3
from flask import Flask
from flask_restful import Api

from selfprivacy_api.resources.users import Users
from selfprivacy_api.resources.common import DecryptDisk


def create_app():
    app = Flask(__name__)
    api = Api(app)

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
