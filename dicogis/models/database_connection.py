#! python3  # noqa: E265

"""
    Dataset model

"""

# ############################################################################
# ######### Libraries #############
# #################################

# Standard library
from dataclasses import dataclass
from typing import Optional

# 3rd party
import pgserviceparser

# package
from dicogis.__about__ import __title_clean__


# ############################################################################
# ######### Classes #############
# ###############################
@dataclass
class DatabaseConnection:
    """Database connection abstraction model."""

    name: Optional[str] = None
    database_name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    service_name: Optional[str] = None
    user_name: Optional[str] = None
    user_password: Optional[str] = None
    # spatial extension
    is_esri_sde: bool = False
    is_postgis: bool = True
    # SGBD properties
    sgbd_schemas: Optional[set[str]] = None
    sgbd_version: Optional[str] = None
    # special
    state_msg: Optional[str] = None

    @property
    def pg_connection_string(self) -> str:
        """Get PostgreSQL connection string.

        See: https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING.
        Structure: host=localhost port=5432 dbname=mydb connect_timeout=10

        Returns:
            str: Connection string for PostgreSQL

        """
        if (
            isinstance(self.service_name, str)
            and self.service_name in pgserviceparser.service_names()
        ):
            return f"PG:service={self.service_name} application_name={__title_clean__}"
        else:
            return (
                f"host={self.host} dbname={self.database_name} user={self.user_name} "
                f"password={self.user_password} port={self.port} "
                f"application_name={__title_clean__}"
            )

    @property
    def pg_connection_uri(self) -> str:
        """Get PostgreSQL connection URI.

        See: https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING.
        Structure: postgresql://[userspec@][hostspec][/dbname][?paramspec]

        Returns:
            str: Connection URI for PostgreSQL
        """
        if (
            isinstance(self.service_name, str)
            and self.service_name in pgserviceparser.service_names()
        ):
            return f"postgresql://?service={self.service_name}&application_name={__title_clean__}"
        else:
            return (
                f"postgresql://{self.user_name}:{self.user_password}@{self.host}:{self.port}/"
                f"{self.database_name}?application_name={__title_clean__}"
            )
