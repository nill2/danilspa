import unittest
from unittest.mock import patch, MagicMock
from flask_testing import TestCase
from app import create_app


class TestAppRoutes(TestCase):
    def create_app(self):
        # Call the Flask application factory to create the app instance
        app = create_app()
        return app

    def test_index_route(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assert_template_used('index.html')

    def test_profile_route(self):
        response = self.client.get('/profile')
        self.assertEqual(response.status_code, 200)
        self.assert_template_used('profile.html')

    # Add tests for other routes


class TestMongoDBInteraction(unittest.TestCase):
    @patch('app.main.MongoClient')
    def test_mongo_connection(self, mock_mongo_client):
        mock_client_instance = MagicMock()
        mock_mongo_client.return_value = mock_client_instance

        # Add test for connecting to MongoDB

    # Add more tests for MongoDB interaction


if __name__ == '__main__':
    unittest.main()
