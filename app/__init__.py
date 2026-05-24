from flask import Flask

from app.config import load_app_config
from app.routes import bp
from app.services.places import PhotonPlaceService

APP_ROOT = "/travel-profile-tool"


def create_app(config_path: str = "config/travel-profile-tool.yml") -> Flask:
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
        static_url_path=f"{APP_ROOT}/static",
    )

    app_config = load_app_config(config_path)
    app.config["APP_CONFIG"] = app_config
    app.config["PLACE_SERVICE"] = PhotonPlaceService(app_config.place_api)

    app.register_blueprint(bp)
    return app
