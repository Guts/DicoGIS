#! python3

"""
    Usage from the repo root folder:
        python -m unittest tests.test_database_connection
"""

# #############################################################################
# ########## Libraries #############
# ##################################


# Standard library
import unittest
from unittest.mock import MagicMock, patch

# project
from dicogis.__about__ import __title_clean__
from dicogis.models.database_connection import DatabaseConnection


class TestDatabaseConnection(unittest.TestCase):
    """Unit tests for the DatabaseConnection class."""

    def setUp(self) -> None:
        """Set up a sample DatabaseConnection instance for testing."""
        self.db_conn = DatabaseConnection(
            name="test_conn",
            database_name="test_db",
            host="localhost",
            port=5432,
            service_name="test_service",
            user_name="test_user",
            user_password="test_password",
            is_esri_sde=False,
            is_postgis=True,
            sgbd_schemas={"public"},
            sgbd_version="13",
            state_msg="active",
        )

    def test_connection_params_as_dict(self) -> None:
        """Test the connection_params_as_dict property."""
        expected_result = {
            "dbname": "test_db",
            "host": "localhost",
            "port": 5432,
            "user": "test_user",
            "password": "test_password",
        }
        self.assertEqual(self.db_conn.connection_params_as_dict, expected_result)

    @patch("pgserviceparser.service_names", return_value=["test_service"])
    def test_pg_connection_string_with_service(
        self, mock_service_names: MagicMock
    ) -> None:
        """Test the pg_connection_string property with a valid service name."""
        expected_result = f"PG:service=test_service application_name={__title_clean__}"
        self.assertEqual(self.db_conn.pg_connection_string, expected_result)

    @patch("pgserviceparser.service_names", return_value=[])
    def test_pg_connection_string_without_service(
        self, mock_service_names: MagicMock
    ) -> None:
        """Test the pg_connection_string property without a valid service name."""
        expected_result = (
            f"host=localhost dbname=test_db user=test_user password=test_password "
            f"port=5432 application_name={__title_clean__}"
        )
        self.assertEqual(self.db_conn.pg_connection_string, expected_result)

    @patch("pgserviceparser.service_names", return_value=["test_service"])
    def test_pg_connection_uri_with_service(
        self, mock_service_names: MagicMock
    ) -> None:
        """Test the pg_connection_uri property with a valid service name."""
        expected_result = (
            f"postgresql://?service=test_service&application_name={__title_clean__}"
        )
        self.assertEqual(self.db_conn.pg_connection_uri, expected_result)

    @patch("pgserviceparser.service_names", return_value=[])
    def test_pg_connection_uri_without_service(
        self, mock_service_names: MagicMock
    ) -> None:
        """Test the pg_connection_uri property without a valid service name."""
        expected_result = (
            f"postgresql://{self.db_conn.user_name}:{self.db_conn.user_password}@{self.db_conn.host}:{self.db_conn.port}/"
            f"{self.db_conn.database_name}?application_name={__title_clean__}"
        )
        self.assertEqual(self.db_conn.pg_connection_uri, expected_result)

    @patch("pgserviceparser.write_service")
    @patch("pgserviceparser.conf_path", return_value="/fake/path/.pg_service.conf")
    def test_store_in_pgservice_file_success(
        self, mock_conf_path: MagicMock, mock_write_service: MagicMock
    ) -> None:
        """Test the store_in_pgservice_file method for a successful save operation."""
        mock_write_service.return_value = True
        status, message = self.db_conn.store_in_pgservice_file()
        self.assertTrue(status)
        self.assertEqual(
            message, f"{self.db_conn.service_name} saved to /fake/path/.pg_service.conf"
        )

    @patch("pgserviceparser.write_service", side_effect=Exception("write error"))
    @patch("pgserviceparser.conf_path", return_value="/fake/path/.pg_service.conf")
    def test_store_in_pgservice_file_failure(
        self, mock_conf_path: MagicMock, mock_write_service: MagicMock
    ) -> None:
        """Test the store_in_pgservice_file method for a failed save operation."""
        status, message = self.db_conn.store_in_pgservice_file()
        self.assertFalse(status)
        self.assertIn(
            "Saving database connection as service in /fake/path/.pg_service.conf failed.",
            message,
        )
        self.assertIn("write error", message)


if __name__ == "__main__":
    unittest.main()
