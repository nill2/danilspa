'''
Module Name: main.py
Description:
    This module defines routes and functions for a Flask application
    that interacts with MongoDB to display images.
'''


import base64
import os
import subprocess
from flask import Blueprint, render_template, Response
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure


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
    '''
    getting the lastest image from the database
    '''
    try:
        # Connect to MongoDB
        client = MongoClient(MONGO_HOST)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]

        # Get the last recorded picture document from the collection
        last_picture = collection.find_one(sort=[('_id', -1)])
        if last_picture:
            # Get the picture data from the 'data' field
            picture_data = last_picture['data']
            # Encode the picture data to Base64
            encoded_picture_data = base64.b64encode(picture_data).decode('utf-8')
            return Response(encoded_picture_data, mimetype='text/plain')
        return "Couldn't find a picture"

    except ConnectionFailure as e:
        return f"Error connecting to MongoDB: {e}"
    finally:
        # Close MongoDB connection
        if client:
            client.close()