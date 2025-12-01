"""Initialize and configure the Flask application.

This module creates the Flask app instance using the application
factory pattern. It loads environment variables, exposes configuration
values to templates, and registers all blueprints.
"""

import os
from flask import Flask
from dotenv import load_dotenv
import pymongo  # FIX: import module, not symbol

# Correct blueprint imports
from .main import main_bp
from .auth import auth as auth_bp


def create_app() -> Flask:
    """Create and configure the Flask application."""
    load_dotenv()

    app = Flask(__name__, instance_relative_config=True)
    app.debug = True

    app.config["FTP_DOMAIN"] = os.getenv("FTP_DOMAIN")

    # --- MongoDB Initialization ---
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")

    # Test patch will correctly catch this:
    # @patch("pymongo.MongoClient")
    client = pymongo.MongoClient(mongo_uri)

    db_name = os.getenv("MONGO_DB", "cctv_db")
    db = client[db_name]

    app.db = {
        "face_collection": db.get_collection("faces"),
        "known_collection": db.get_collection("known_people"),
        "photos_collection": db.get_collection("photos"),
    }

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)

    return app
