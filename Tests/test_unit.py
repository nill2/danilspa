"""
Unit tests for testing routes and MongoDB interaction in the Flask application.

This module contains unit tests for testing the functionality of routes and MongoDB interaction
in the Flask application. It includes two main test classes:
TestAppRoutes and TestMongoDBInteraction.

TestAppRoutes:
    A subclass of Flask's TestCase for testing Flask routes.
    It includes test cases for the index route ('/') and the profile route ('/profile').
    Other routes can be added as needed.

TestMongoDBInteraction:
    A subclass of unittest.TestCase for testing MongoDB interaction.
    It includes a test case for testing the connection to MongoDB.
    Additional test cases for MongoDB interaction can be added as needed.

Usage:
    Run this module to execute the unit  tests.
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock
from flask_testing import TestCase

# Add the parent directory of the current file to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Now you can import the app module
from app import create_app  # pylint: disable=all  # noqa


class TestAppRoutes(TestCase):
    """
    Test cases for testing Flask routes.

    This class includes test cases for various routes in the Flask application,
    such as the index route ('/') and the profile route ('/profile').
    """

    def create_app(self):
        """
        Create a Flask app instance.

        Returns:
            app: An instance of the Flask application.
        """
        app = create_app()
        return app

    def test_index_route(self):
        """
        Test the index route ('/').

        This test case verifies that the index route returns a status code of 200
        and uses the correct HTML template ('index.html').
        """
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assert_template_used('index.html')

    def test_profile_route(self):
        """
        Test the profile route ('/profile').

        This test case verifies that the profile route returns a status code of 200
        and uses the correct HTML template ('profile.html').
        """
        response = self.client.get('/profile')
        self.assertEqual(response.status_code, 200)
        self.assert_template_used('profile.html')


class TestMongoDBInteraction(unittest.TestCase):
    """
    Test cases for testing MongoDB interaction.

    This class includes test cases for interacting with MongoDB,
    such as testing the connection to MongoDB.
    """

    @patch('app.main.MongoClient')
    def test_mongo_connection(self, mock_mongo_client):
        """
        Test MongoDB connection.

        This test case verifies that the application can connect to MongoDB
        by mocking the MongoClient and testing the connection.
        """
        mock_client_instance = MagicMock()
        mock_mongo_client.return_value = mock_client_instance
        # Add test for connecting to MongoDB


if __name__ == '__main__':
    unittest.main()
