"""Initialize and configure the Flask application."""

from flask import Flask
from .main import main as main_blueprint
from .auth import auth as auth_blueprint


def create_app() -> Flask:  # test_config=None
    """Create and configure the Flask application."""
    app = Flask(__name__, instance_relative_config=True)

    # Enable debugging mode
    app.debug = True

    # Register blueprints
    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint)

    return app
