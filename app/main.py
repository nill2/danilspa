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
from botocore.exceptions import ClientError
from datetime import datetime
import json


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
        s3 = boto3.client('s3',
                          aws_access_key_id=AWS_ACCESS_KEY,
                          aws_secret_access_key=AWS_SECRET_KEY)

        # Delete the file from the S3 bucket
        s3.delete_object(Bucket=bucket_name, Key=s3_key)
        logger.info("Deleted file from S3: %s", s3_file_url)
    except ClientError as e:
        logger.error("Error deleting file from S3: %s", e)


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


@main.route('/faces')
def faces():
    '''
    Page to display images from the faces collection with their dates
    '''
    try:
        # Connect to MongoDB
        client = MongoClient(MONGO_HOST)
        db = client[DATABASE_NAME]
        collection = db["nill-home-faces"]

        # Fetch all documents and include the `bsonTime` along with image data
        images_with_dates = []
        for doc in collection.find().sort('_id', -1):  # Sort by `_id` descending
            image_data = {
                "image_id": str(doc["filename"]),  # Use _id as a unique identifier
                "bsonTime": doc.get("bsonTime", "Unknown")
            }
            images_with_dates.append(image_data)

        logger.info(f"Fetched {len(images_with_dates)} images with dates for faces page.")
        return render_template('faces.html', images_with_dates=images_with_dates)
    except ConnectionFailure as e:
        logger.error(f"Error connecting to MongoDB: {e}")
        return "Error loading faces page", 500
    except Exception as e:
        logger.error(f"Unexpected error loading faces page: {e}")
        return "Unexpected error occurred", 500
    finally:
        if 'client' in locals() and client:
            client.close()


@main.route('/fetch_face_image/<int:image_index>')
def fetch_face_image(image_index):  # noqa
    '''
    Fetch an image data from MongoDB (nill-home-faces collection) by index
    '''
    try:
        # Connect to MongoDB
        client = MongoClient(MONGO_HOST)
        db = client[DATABASE_NAME]
        collection = db["nill-home-faces"]

        # Fetch and validate image list
        images = list(collection.find().sort('_id', -1))  # Sort by `_id` descending
        logger.info(f"Number of images fetched from MongoDB: {len(images)}")
        if not images:
            logger.error("No images found in the collection.")
            return "No images found", 404

        # Validate index
        logger.info(f"Requested image index: {image_index}")
        if not (0 <= image_index < len(images)):
            logger.error(f"Invalid image index: {image_index}. Must be between 0 and {len(images) - 1}.")
            return "Invalid image index", 404

        # Fetch the document at the given index
        image_doc = images[image_index]
        # logger.info(f"Fetched document: {image_doc}")

        # Prepare response data
        bson_time = image_doc.get("bsonTime")
        logger.info(f"bsonTime field value: {bson_time}")
        logger.info(f"bsonTime type: {type(bson_time)}")
        response_data = {
            "imageId": str(image_doc["filename"]),
            # Convert bsonTime (datetime) to string if it's a datetime object
            "bsonTime": bson_time.strftime('%Y-%m-%d %H:%M:%S') if isinstance(bson_time, datetime) else "Unknown"
        }

        # Check if `s3_file_url` exists and is valid
        if "s3_file_url" in image_doc and image_doc["s3_file_url"]:
            s3_file_url = image_doc["s3_file_url"]
            logger.info(f"Fetching face image from S3: {s3_file_url}")
            try:
                bucket_name = s3_file_url.split("//")[1].split(".")[0]
                s3_key = s3_file_url.split(bucket_name + ".s3.amazonaws.com/")[1]
                s3 = boto3.client('s3',
                                  aws_access_key_id=AWS_ACCESS_KEY,
                                  aws_secret_access_key=AWS_SECRET_KEY)
                local_temp_file_path = 'temp_face_image.jpg'
                s3.download_file(bucket_name, s3_key, local_temp_file_path)
                with open(local_temp_file_path, 'rb') as file:
                    image_content = file.read()
                os.remove(local_temp_file_path)
                encoded_image_data = base64.b64encode(image_content).decode('utf-8')

                # Include image data in the response
                response_data["imageData"] = encoded_image_data
                return Response(json.dumps(response_data), mimetype='application/json')
            except ClientError as e:
                logger.error(f"Error fetching image from S3: {e}")
                return "Error fetching image from S3", 500
        elif "data" in image_doc and image_doc["data"]:
            # Get image from MongoDB's `data` field
            logger.info("Fetching image from MongoDB data field.")
            picture_data = image_doc["data"]
            try:
                encoded_picture_data = base64.b64encode(picture_data).decode('utf-8')

                # Include image data in the response
                response_data["imageData"] = encoded_picture_data
                return Response(json.dumps(response_data), mimetype='application/json')
            except Exception as e:
                logger.error(f"Error encoding image data: {e}")
                return "Error processing image data", 500
        else:
            logger.error(f"Document at index {image_index} has no valid fields (s3_file_url or data).")
            return "Image data not found", 404
    except Exception as e:  # pylint: disable=W0718
        logger.error(f"Unexpected error fetching face image: {e}")
        return "Unexpected error occurred", 500
    finally:
        if 'client' in locals() and client:
            client.close()


@main.route('/fetch_image')
def fetch_image():  # pylint: disable=R0914
    '''
    Fetch an image data from MongoDB and Image itself from S3
    '''
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
                logger.info("getting pic from S3: %s", s3_file_url)
                try:
                    # Extract bucket name and key from the S3 file URL
                    bucket_name = s3_file_url.split("//")[1].split(".")[0]
                    s3_key = s3_file_url.split(bucket_name + ".s3.amazonaws.com/")[1]

                    # Create an S3 client
                    s3 = boto3.client('s3',
                                      aws_access_key_id=AWS_ACCESS_KEY,
                                      aws_secret_access_key=AWS_SECRET_KEY)

                    # Download the file from the S3 bucket to a temporary file
                    local_temp_file_path = 'temp_image.jpg'
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
                except ClientError as e:
                    logger.error("Error downloading file from S3: %s", e)
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
    except Exception as e:  # pylint: disable=W0718
        logger.error("Error fetching image: %s", e)
        return "Error fetching image"
    finally:
        # Close MongoDB connection
        if client:
            client.close()
