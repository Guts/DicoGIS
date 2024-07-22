#! python3  # noqa: E265

"""Model for database connection."""

# ############################################################################
# ######### Libraries #############
# #################################

# Standard library
import logging
from dataclasses import dataclass
from typing import Optional

# 3rd party
import pgserviceparser

# package
from dicogis.__about__ import __title_clean__

# ##############################################################################
# ############ Globals ############
# #################################

# LOG
logger = logging.getLogger(__name__)


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
    def connection_params_as_dict(self) -> dict | None:
        """Return connection parameters as dictionary. Useful to create a service in a
            pg_service.conf file.

        Returns:
            connection parameters as dict
        """
        as_dict = {
            "dbname": str(self.database_name) if self.database_name else None,
            "host": str(self.host) if self.host else None,
            "port": str(self.port) if self.port else None,
            "user": str(self.user_name) if self.user_name else None,
            "password": str(self.user_password) if self.user_password else None,
        }

        return {key: value for (key, value) in as_dict.items() if value is not None}

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

    def store_in_pgservice_file(self) -> tuple[bool, str]:
        """Store database connection to service file (typically on Linux
            ~/.pg_service.conf).

        Returns:
            a tuple with the store status and a log message
        """
        try:
            if not self.connection_params_as_dict:
                raise ValueError(
                    "Database connection results as an empty dictionary and can't be saved."
                )

            pgserviceparser.write_service(
                service_name=self.service_name,
                settings=self.connection_params_as_dict,
                add_if_not_exists=True,
            )
            return True, f"{self.service_name} saved to {pgserviceparser.conf_path()}"
        except Exception as err:
            err_msg = (
                "Saving database connection as service in "
                f"{pgserviceparser.conf_path()} failed. Trace: {err}"
            )
            logger.error(err_msg, stack_info=True)
            return False, err_msg
