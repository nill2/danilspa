'''
Module Name: main.py
Description:
    This module defines routes and functions for a Flask application
    that interacts with MongoDB to display images.
'''


import base64
import os
import subprocess
import logging
import boto3
from flask import Blueprint, render_template, Response
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure


# Configure the logger (optional)
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

# Define the logger
logger = logging.getLogger(__name__)


main = Blueprint('main', __name__)

# MongoDB connection string
MONGO_HOST = "localhost"
if "MONGO_HOST" in os.environ:
    MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
    print("Getting from env vars"+MONGO_HOST)
else:
    try:
        # Run the vlt command and capture its output
        VLT_COMMAND = "vlt secrets get --plaintext MONGO_HOST"
        MONGO_HOST = subprocess.check_output(VLT_COMMAND, shell=True, text=True)
        print("Value from hashicorp for MONGO_HOST: "+str(MONGO_HOST))
    except subprocess.CalledProcessError as hashi_e:
        # Handle errors, e.g., if the secret does not exist
        print(f"Error: {hashi_e}")
# MongoDB database name
DATABASE_NAME = "nill-home"
# MongoDB collection name where the pictures are stored
COLLECTION_NAME = "nill-home-photos"


AWS_ACCESS_KEY = None
if "AWS_ACCESS_KEY" in os.environ:
    AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY", None)
    print("Getting AWS_ACCESS_KEY from env vars: "+AWS_ACCESS_KEY)
else:
    try:
        # Run the vlt command and capture its output
        VLT_COMMAND = "vlt secrets get --plaintext AWS_ACCESS_KEY"
        AWS_ACCESS_KEY = subprocess.check_output(VLT_COMMAND, shell=True, text=True)
        print("Value from hashicorp for MONGO_HOST: "+str(AWS_ACCESS_KEY))
    except subprocess.CalledProcessError as hashi_e:
        # Handle errors, e.g., if the secret does not exist
        print(f"Error: {hashi_e}")

AWS_SECRET_KEY = None
if "AWS_SECRET_KEY" in os.environ:
    AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY", None)
    print("Getting AWS_SECRET_KEY from env vars: "+AWS_SECRET_KEY)
else:
    try:
        # Run the vlt command and capture its output
        VLT_COMMAND = "vlt secrets get --plaintext AWS_SECRET_KEY"
        AWS_SECRET_KEY = subprocess.check_output(VLT_COMMAND, shell=True, text=True)
        print("Value from hashicorp for MONGO_HOST: "+str(AWS_SECRET_KEY))
    except subprocess.CalledProcessError as hashi_e:
        # Handle errors, e.g., if the secret does not exist
        print(f"Error: {hashi_e}")

AWS_BUCKET_NAME = "nill-home-photos"


def delete_s3_file(s3_file_url):
    """
    Deletes a file from an S3 bucket based on its URL.

    Args:
        s3_file_url (str): The URL of the file in the S3 bucket.
    """
    try:
        # Extract bucket name and key from the S3 file URL
        bucket_name = s3_file_url.split("//")[1].split(".")[0]
        s3_key = s3_file_url.split(bucket_name + ".s3.amazonaws.com/")[1]

        # Create an S3 client
        s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)

        # Delete the file from the S3 bucket
        s3.delete_object(Bucket=bucket_name, Key=s3_key)
        logger.info(f"Deleted file from S3: {s3_file_url}")
    except Exception as e:
        logger.error(f"Error deleting file from S3: {e}")


@main.route('/')
def index():
    '''
    Default page
    '''
    return render_template('index.html')


@main.route('/profile')
def profile():
    '''
    stub so far
    '''
    return render_template('profile.html')


@main.route('/cctv')
def cctv():
    '''
    Define the main.cctv endpoint
    '''
    return render_template('cctv.html')


@main.route('/fetch_image')
def fetch_image():
    try:
        # Connect to MongoDB
        client = MongoClient(MONGO_HOST)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]

        # Get the last recorded picture document from the collection
        last_picture = collection.find_one(sort=[('_id', -1)])
        if last_picture:
            if last_picture.get("s3_file_url"):
                # Extract the S3 file URL from the document
                s3_file_url = last_picture["s3_file_url"]
                logger.info("getting pic from S3: %s" % s3_file_url)
                try:
                    # Extract bucket name and key from the S3 file URL
                    bucket_name = s3_file_url.split("//")[1].split(".")[0]
                    s3_key = s3_file_url.split(bucket_name + ".s3.amazonaws.com/")[1]

                    # Create an S3 client
                    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)

                    # Download the file from the S3 bucket to a temporary file
                    local_temp_file_path = 'temp_image.jpg'  # Use a temporary file to store the downloaded image
                    s3.download_file(bucket_name, s3_key, local_temp_file_path)
                    
                    # Read the content of the downloaded file
                    with open(local_temp_file_path, 'rb') as file:
                        image_content = file.read()

                    # Encode the image content to Base64
                    encoded_image_data = base64.b64encode(image_content).decode('utf-8')

                    # Return the Base64 encoded image data
                    response = Response(encoded_image_data, mimetype='text/plain')

                    # After processing the image, delete the temporary file
                    if os.path.exists(local_temp_file_path):
                        os.remove(local_temp_file_path)
                        print(f"Temporary file deleted: {local_temp_file_path}")

                    return response
                except Exception as e:
                    logger.error(f"Error downloading file from S3: {e}")
            else:
                # Get the picture data from the 'data' field
                logger.info("getting pic from from the data field from MongoDB")
                picture_data = last_picture['data']
                # Encode the picture data to Base64
                encoded_picture_data = base64.b64encode(picture_data).decode('utf-8')
                response = Response(encoded_picture_data, mimetype='text/plain')
                return response
        return "Couldn't find a picture"
    except ConnectionFailure as e:
        return f"Error connecting to MongoDB: {e}"
    except Exception as e:
        logger.error(f"Error fetching image: {e}")
        return "Error fetching image"
    finally:
        # Close MongoDB connection
        if client:
            client.close()
