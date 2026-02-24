#! python3  # noqa: E265

"""Simple function to load database configuration files (= ini structure)."""

# #############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import logging
from configparser import ConfigParser
from pathlib import Path

# #############################################################################
# ########## Globals ###############
# ##################################

logger = logging.getLogger(__name__)


# ##############################################################################
# ######### Functions ##############
# ##################################


def read_db_conf(dbconf_path: Path) -> list | dict:
    """Read databases configuration files and return parameters as list of dictionaries.

    Args:
        dbconf_path (Path): filepath to *.dbconf file

    Raises:
        TypeError: if input filepath is not an instance of pathlib.Path
        FileExistsError: if input file is not reachable

    Returns:
        Union[list, dict]: list of dictionary/ies with database parameters

    :Example:

        .. code-block:: python

            # here comes an example in Python
            pprint(read_db_conf("./sample.dbconf"))
            {
                "name": "database_name",
                "host": "database_server_url",
                "port": "5432",
                "username": "db_user_name",
                "password": "db_user_password",
                "schemas": "db_schemas",
                "esri_sde": False
            }

    """
    # checks
    if not isinstance(dbconf_path, Path):
        raise TypeError(
            "dbconf_path must be a {} instance, not {}".format(
                type(Path), type(dbconf_path)
            )
        )

    if not dbconf_path.is_file():
        raise FileExistsError("{} doesn't exist.")

    # prepare output var
    li_dabatases = []

    # open the file
    conf_reader = ConfigParser()
    conf_reader.read(str(dbconf_path.resolve()))

    for db in conf_reader.sections():
        try:
            database = {
                "name": db,
                "host": conf_reader.get(section=db, option="host"),
                "port": conf_reader.get(section=db, option="port"),
                "username": conf_reader.get(section=db, option="user"),
                "password": conf_reader.get(section=db, option="password"),
                "schemas": conf_reader.get(section=db, option="schemas"),
                "esri_sde": 0,
            }
            li_dabatases.append(db)
            logger.debug(
                "Configuration for database {} found into {}".format(
                    database.get("name"), dbconf_path.resolve()
                )
            )
        except Exception as err:
            logger.error(err)
            continue

    return li_dabatases
