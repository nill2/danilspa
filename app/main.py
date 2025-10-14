"""
Module Name: main.py.

Description:
    Flask Blueprint defining routes for the personal page, CCTV, and face recognition features.
    Integrates with MongoDB and AWS S3 for CCTV image storage and retrieval.
    Machine Learning (face recognition) functionality now uses backend API calls via FTP_IP.
"""

from __future__ import annotations

import base64
import os
import subprocess
import logging
import boto3
import json
import requests
from flask import Blueprint, render_template, Response, jsonify, request
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from botocore.exceptions import ClientError
from datetime import datetime
from typing import Any

# -------------------------------------------------------------------
# Logging setup
# -------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

main = Blueprint("main", __name__)

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
if MONGO_HOST == "localhost":
    try:
        MONGO_HOST = subprocess.check_output(
            "vlt secrets get --plaintext MONGO_HOST", shell=True, text=True
        ).strip()
        logger.info("Loaded MONGO_HOST from Vault: %s", MONGO_HOST)
    except subprocess.CalledProcessError:
        logger.warning("Falling back to localhost for MONGO_HOST")

FTP_IP = os.getenv("FTP_IP", "127.0.0.1")
DATABASE_NAME = "nill-home"
COLLECTION_NAME = "nill-home-photos"


# -------------------------------------------------------------------
# AWS configuration
# -------------------------------------------------------------------
def get_secret_from_vault_or_env(var_name: str) -> str | None:
    """Retrieve secret value either from environment or Vault."""
    value = os.getenv(var_name)
    if value:
        return value
    try:
        return subprocess.check_output(
            f"vlt secrets get --plaintext {var_name}", shell=True, text=True
        ).strip()
    except subprocess.CalledProcessError:
        logger.warning(f"Failed to get {var_name} from Vault")
        return None


AWS_ACCESS_KEY = get_secret_from_vault_or_env("AWS_ACCESS_KEY")
AWS_SECRET_KEY = get_secret_from_vault_or_env("AWS_SECRET_KEY")
AWS_BUCKET_NAME = "nill-home-photos"


# -------------------------------------------------------------------
# Utility functions
# -------------------------------------------------------------------
def delete_s3_file(s3_file_url: str) -> None:
    """Delete a file from an S3 bucket based on its URL."""
    try:
        bucket_name = s3_file_url.split("//")[1].split(".")[0]
        s3_key = s3_file_url.split(bucket_name + ".s3.amazonaws.com/")[1]
        s3 = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
        )
        s3.delete_object(Bucket=bucket_name, Key=s3_key)
        logger.info("Deleted file from S3: %s", s3_file_url)
    except ClientError as e:
        logger.error("Error deleting file from S3: %s", e)


# -------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------
@main.route("/")
def index() -> str:
    """Render home (about me) page."""
    return render_template("index.html")


@main.route("/profile")
def profile() -> str:
    """Render profile page."""
    return render_template("profile.html")


@main.route("/cctv")
def cctv() -> str:
    """Render CCTV page."""
    return render_template("cctv.html")


@main.route("/faces")
def faces() -> Response | tuple[str, int]:
    """Display list of known faces with timestamps."""
    try:
        client = MongoClient(MONGO_HOST)
        db = client[DATABASE_NAME]
        collection = db["nill-home-faces"]

        images_with_dates = [
            {
                "image_id": str(doc.get("filename", "")),
                "bsonTime": doc.get("bsonTime", "Unknown"),
            }
            for doc in collection.find().sort("_id", -1)
        ]

        return render_template("faces.html", images_with_dates=images_with_dates)
    except ConnectionFailure as e:
        logger.error("MongoDB connection failed: %s", e)
        return "Database error", 500
    except Exception as e:
        logger.error("Unexpected error in /faces: %s", e)
        return "Unexpected error", 500
    finally:
        if "client" in locals():
            client.close()


# -------------------------------------------------------------------
# ML (Backend API Proxies)
# -------------------------------------------------------------------
@main.route("/ml-known")
def ml_known() -> str:
    """Render ML known faces search page."""
    return render_template("ml_known.html")


@main.route("/api/ml/known-faces", methods=["GET"])
def api_ml_known_faces() -> Response:
    """Get list of known face names from backend API."""
    try:
        response = requests.get(f"http://{FTP_IP}:8001/faces/known_names", timeout=15)
        return Response(
            response.content, status=response.status_code, mimetype="application/json"
        )
    except Exception as e:
        logger.error("Error fetching known faces: %s", e)
        return jsonify({"error": "Failed to fetch known faces"}), 500


@main.route("/api/ml/search", methods=["POST"])
def api_ml_search() -> Response:
    """Proxy search for known or unknown faces via backend API."""
    selected = request.json or []
    base_url = f"http://{FTP_IP}:8001"

    try:
        if not selected:
            response = requests.get(f"{base_url}/faces/unknown", timeout=15)
        else:
            response = requests.post(
                f"{base_url}/faces/known",
                json=selected,
                headers={"Content-Type": "application/json"},
                timeout=15,
            )
        return Response(
            response.content, status=response.status_code, mimetype="application/json"
        )
    except Exception as e:
        logger.error("Error calling backend ML API: %s", e)
        return jsonify({"error": "Backend API call failed"}), 500


# -------------------------------------------------------------------
# Fetch images (used by CCTV and Faces pages)
# -------------------------------------------------------------------
@main.route("/fetch_face_image/<int:image_index>")
def fetch_face_image(image_index: int) -> Response | tuple[str, int]:
    """Fetch a face image by index from MongoDB or S3."""
    try:
        client = MongoClient(MONGO_HOST)
        db = client[DATABASE_NAME]
        collection = db["nill-home-faces"]
        images = list(collection.find().sort("_id", -1))

        if not (0 <= image_index < len(images)):
            return "Invalid image index", 404

        doc = images[image_index]
        response_data: dict[str, Any] = {
            "imageId": str(doc.get("filename", "")),
            "bsonTime": (
                doc["bsonTime"].strftime("%Y-%m-%d %H:%M:%S")
                if isinstance(doc.get("bsonTime"), datetime)
                else "Unknown"
            ),
        }

        if doc.get("s3_file_url"):
            s3_file_url = doc["s3_file_url"]
            bucket_name = s3_file_url.split("//")[1].split(".")[0]
            s3_key = s3_file_url.split(bucket_name + ".s3.amazonaws.com/")[1]
            s3 = boto3.client(
                "s3",
                aws_access_key_id=AWS_ACCESS_KEY,
                aws_secret_access_key=AWS_SECRET_KEY,
            )
            temp_file = "temp_face_image.jpg"
            s3.download_file(bucket_name, s3_key, temp_file)
            with open(temp_file, "rb") as f:
                encoded_data = base64.b64encode(f.read()).decode("utf-8")
            os.remove(temp_file)
            response_data["imageData"] = encoded_data
        elif doc.get("data"):
            encoded_data = base64.b64encode(doc["data"]).decode("utf-8")
            response_data["imageData"] = encoded_data
        else:
            return "Image data not found", 404

        return Response(json.dumps(response_data), mimetype="application/json")
    except Exception as e:
        logger.error("Error fetching face image: %s", e)
        return "Error fetching image", 500
    finally:
        if "client" in locals():
            client.close()


@main.route("/fetch_image")
def fetch_image() -> Response | tuple[str, int]:
    """Fetch the latest CCTV image."""
    try:
        client = MongoClient(MONGO_HOST)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        last_picture = collection.find_one(sort=[("_id", -1)])

        if not last_picture:
            return "No picture found", 404

        if last_picture.get("s3_file_url"):
            s3_url = last_picture["s3_file_url"]
            bucket_name = s3_url.split("//")[1].split(".")[0]
            s3_key = s3_url.split(bucket_name + ".s3.amazonaws.com/")[1]
            s3 = boto3.client(
                "s3",
                aws_access_key_id=AWS_ACCESS_KEY,
                aws_secret_access_key=AWS_SECRET_KEY,
            )
            temp_file = "temp_image.jpg"
            s3.download_file(bucket_name, s3_key, temp_file)
            with open(temp_file, "rb") as f:
                encoded_data = base64.b64encode(f.read()).decode("utf-8")
            os.remove(temp_file)
        else:
            encoded_data = base64.b64encode(last_picture["data"]).decode("utf-8")

        return Response(encoded_data, mimetype="text/plain")
    except Exception as e:
        logger.error("Error fetching latest CCTV image: %s", e)
        return "Error fetching image", 500
    finally:
        if "client" in locals():
            client.close()
