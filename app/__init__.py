"""Initialize and configure the Flask application."""

from flask import Flask
from dotenv import load_dotenv
import os

from .main import main as main_blueprint
from .auth import auth as auth_blueprint


def create_app() -> Flask:
    """Create and configure the Flask application."""
    # ✅ Load environment variables
    load_dotenv()

    app = Flask(__name__, instance_relative_config=True)
    app.debug = True

    # ✅ Make FTP_DOMAIN available to templates
    app.config["FTP_DOMAIN"] = os.getenv("FTP_DOMAIN")

    # ✅ Register blueprints
    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint)

    return app
