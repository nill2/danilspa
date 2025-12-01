"""Main blueprint defining routes for the website.

This module contains the UI pages (home, profile, CCTV, faces)
and proxy routes that communicate with the backend API instead
of direct MongoDB access.
"""

import os
import logging
import requests
from flask import Blueprint, render_template, jsonify, Response, request

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the blueprint
main_bp = Blueprint("main", __name__)

# Backend API base URL (HTTPS, no ports)
FTP_DOMAIN = os.getenv("FTP_DOMAIN", "nill2.duckdns.org")
BACKEND_BASE_URL = f"https://{FTP_DOMAIN}"

logger.info(f"Using backend API base URL: {BACKEND_BASE_URL}")


# ---------------------------------------------------------
# UI ROUTES
# ---------------------------------------------------------


@main_bp.route("/")
def index() -> str:
    """Render the homepage."""
    return render_template("index.html")


@main_bp.route("/profile")
def profile() -> str:
    """Render the profile page."""
    return render_template("profile.html")


@main_bp.route("/cctv")
def cctv() -> str:
    """Render the CCTV live preview page."""
    return render_template("cctv.html")


@main_bp.route("/faces")
def faces() -> str:
    """Render the faces page."""
    return render_template("faces.html")


# ---------------------------------------------------------
# API PROXY ROUTES (Backend → Frontend)
# ---------------------------------------------------------


@main_bp.route("/api/cctv/latest")
def api_cctv_latest() -> Response:
    """Fetch latest CCTV entry from backend API."""
    try:
        r = requests.get(f"{BACKEND_BASE_URL}/current_cctv", timeout=10)
        return Response(r.content, status=r.status_code, mimetype="application/json")
    except Exception as e:
        logger.error(f"Error fetching CCTV from backend: {e}")
        return jsonify({"error": "Backend unavailable"}), 500


@main_bp.route("/api/faces/all")
def api_faces_all() -> Response:
    """Fetch all detected faces from backend API."""
    try:
        r = requests.get(f"{BACKEND_BASE_URL}/photos_detected_faces", timeout=10)
        return Response(r.content, status=r.status_code, mimetype="application/json")
    except Exception as e:
        logger.error(f"Error fetching detected faces: {e}")
        return jsonify({"error": "Backend unavailable"}), 500


# ---------------------------------------------------------
# ML ROUTES
# ---------------------------------------------------------


@main_bp.route("/ml-known")
def ml_known() -> str:
    """Render the ML known-faces search page."""
    return render_template("ml_known.html", FTP_DOMAIN=FTP_DOMAIN)


@main_bp.route("/api/ml/known-faces")
def api_ml_known_faces() -> Response:
    """Proxy: return list of known face names."""
    try:
        r = requests.get(f"{BACKEND_BASE_URL}/faces/known_names", timeout=10)
        return Response(r.content, status=r.status_code, mimetype="application/json")
    except Exception as e:
        logger.error(f"Error fetching known faces: {e}")
        return jsonify({"error": "Backend unavailable"}), 500


@main_bp.route("/api/ml/search", methods=["POST"])
def api_ml_search() -> Response:
    """Proxy: find known or unknown faces."""
    try:
        payload = request.json or []
        if not payload:
            r = requests.get(f"{BACKEND_BASE_URL}/faces/unknown", timeout=10)
        else:
            r = requests.post(
                f"{BACKEND_BASE_URL}/faces/known",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
        return Response(r.content, status=r.status_code, mimetype="application/json")
    except Exception as e:
        logger.error(f"Error calling ML backend: {e}")
        return jsonify({"error": "Backend unavailable"}), 500
