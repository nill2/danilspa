"""WSGI entry point for the Flask application."""

import os
import logging
from dotenv import load_dotenv
from app import create_app

# ✅ Load environment variables from .env
load_dotenv()

# ✅ Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Show environment variable values for verification
ftp_ip = os.getenv("FTP_IP")
ftp_domain = os.getenv("FTP_DOMAIN")
mongo_uri = os.getenv("MONGO_URI")

logger.info("🚀 Starting Flask app with environment variables:")
logger.info(f"FTP_IP = {ftp_ip}")
if mongo_uri:
    logger.info(f"MONGO_URI (truncated) = {mongo_uri[:40]}...")

# ✅ Create the app
app = create_app()

# ✅ Optional: run directly (for local testing)
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Flask app running on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
