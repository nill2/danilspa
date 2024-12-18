"""App launcher."""

import os
import subprocess
import pyroscope  # pylint: disable=import-error
from app import create_app


PYROSCOPE_SERVER_ADDRESS = "http://138.2.149.246:4040"

if "PYROSCOPE_SERVER_ADDRESS" in os.environ:
    PYROSCOPE_SERVER_ADDRESS = os.getenv("PYROSCOPE_SERVER_ADDRESS", None)
    print("Getting PYROSCOPE_SERVER_ADDRESS from env vars: " + PYROSCOPE_SERVER_ADDRESS)
else:
    try:
        # Run the vlt command and capture its output
        VLT_COMMAND = "vlt secrets get --plaintext PYROSCOPE_SERVER_ADDRESS"
        PYROSCOPE_SERVER_ADDRESS = subprocess.check_output(
            VLT_COMMAND, shell=True, text=True
        )
        print("Value from hashicorp for MONGO_HOST: " + str(PYROSCOPE_SERVER_ADDRESS))
    except subprocess.CalledProcessError as hashi_e:
        # Handle errors, e.g., if the secret does not exist
        print(f"Error: {hashi_e}")

# Configure Pyroscope
pyroscope.configure(
    application_name="danilspa",
    server_address=PYROSCOPE_SERVER_ADDRESS,
    sample_rate=100,
    detect_subprocesses=True,
    oncpu=True,
    gil_only=True,
    enable_logging=True,
    tags={
        "region": os.getenv("REGION"),
    },
)

app = create_app()
