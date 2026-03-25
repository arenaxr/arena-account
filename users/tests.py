from unittest.mock import MagicMock, patch

from django.test import Client, TestCase


class HealthCheckTests(TestCase):
    def setUp(self):
        self.client = Client()

    @patch('users.api.get_filestore_health')
    @patch('users.api.connection')
    @patch('users.api.get_persist_db')
    def test_health_check_success(self, mock_get_persist_db, mock_connection, mock_filestore):
        # Mock SQLite success
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Mock MongoDB success
        mock_db = MagicMock()
        mock_get_persist_db.return_value = mock_db

        # Mock Filestore success
        mock_filestore.return_value = True

        response = self.client.get('/user/health')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "result": "success",
            "sqlite_status": "healthy",
            "mongo_status": "healthy",
            "filestore_status": "healthy",
        })

    @patch('users.api.get_filestore_health')
    @patch('users.api.connection')
    @patch('users.api.get_persist_db')
    def test_health_check_sqlite_failure(self, mock_get_persist_db, mock_connection, mock_filestore):
        # Mock SQLite failure
        mock_connection.cursor.side_effect = Exception("SQLite error")

        # Mock MongoDB success
        mock_db = MagicMock()
        mock_get_persist_db.return_value = mock_db

        # Mock Filestore success
        mock_filestore.return_value = True

        response = self.client.get('/user/health')

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {
            "result": "failure",
            "sqlite_status": "unhealthy",
            "mongo_status": "healthy",
            "filestore_status": "healthy",
        })

    @patch('users.api.get_filestore_health')
    @patch('users.api.connection')
    @patch('users.api.get_persist_db')
    def test_health_check_mongo_failure(self, mock_get_persist_db, mock_connection, mock_filestore):
        # Mock SQLite success
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Mock MongoDB failure
        mock_get_persist_db.side_effect = Exception("Mongo error")

        # Mock Filestore success
        mock_filestore.return_value = True

        response = self.client.get('/user/health')

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {
            "result": "failure",
            "sqlite_status": "healthy",
            "mongo_status": "unhealthy",
            "filestore_status": "healthy",
        })
