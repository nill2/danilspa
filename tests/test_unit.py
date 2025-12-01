"""
Unit tests for Flask routes and MongoDB interaction.

This module contains tests for:
- Flask route behavior (TestAppRoutes)
- MongoDB client initialization (TestMongoDBInteraction)
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock
from flask_testing import TestCase

# Add the parent directory of the current file to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from app import create_app  # noqa


class TestAppRoutes(TestCase):
    """Test cases for Flask route behavior."""

    def create_app(self):
        """Create a Flask app instance for testing."""
        return create_app()

    def test_index_route(self):
        """Index route should return status 200 and correct template."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assert_template_used("index.html")

    def test_profile_route(self):
        """Profile route should return status 200 and correct template."""
        response = self.client.get("/profile")
        self.assertEqual(response.status_code, 200)
        self.assert_template_used("profile.html")


class TestMongoDBInteraction(unittest.TestCase):
    """Test MongoDB client initialization."""

    @patch("pymongo.MongoClient")
    def test_mongo_connection(self, mock_mongo_client):
        """Mongoclient should be called when create_app() initializes DB."""
        mock_mongo_client.return_value = MagicMock()

        create_app()  # no unused variable now

        mock_mongo_client.assert_called()


if __name__ == "__main__":
    unittest.main()
