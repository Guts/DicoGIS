#! python3  # noqa: E265

"""
    Log management.

    Author: Julien Moura

    See: https://docs.python.org/fr/3/howto/logging.html
"""

# #############################################################################
# ########## Libraries #############
# ##################################


# Standard library
import logging
from getpass import getuser
from logging.handlers import RotatingFileHandler
from os import environ
from pathlib import Path
from platform import architecture
from platform import platform as opersys
from socket import gethostname
from typing import Optional
from urllib.request import getproxies

# modules
from dicogis.__about__ import __title_clean__ as package_name
from dicogis.__about__ import __version__
from dicogis.utils.environment import get_gdal_version, get_proj_version
from dicogis.utils.slugger import sluggy

# #############################################################################
# ########## Globals ###############
# ##################################


logger = logging.getLogger(__name__)  # logs


# #############################################################################
# ########## Classes ###############
# ##################################


class LogManager:
    """Manage logs: configuration, parsing, etc."""

    LOG_FORMAT = logging.Formatter(
        "%(asctime)s || %(levelname)s "
        "|| %(module)s || %(lineno)d "
        "|| %(funcName)s || %(message)s"
    )

    def __init__(
        self,
        console_level: int = logging.WARNING,
        file_level: int = logging.INFO,
        label: str = package_name,
        folder: Optional[Path] = None,
    ):
        """Initialize.

        Args:
            console_level: log level for console handler. Defaults to logging.WARNING.
            file_level: log level for file handler. Defaults to logging.INFO.
            label: log file name. Defaults to package_name.
            folder: where to store log files. Defaults to None.
        """
        # store parameters as attributes
        self.console_level = console_level
        self.file_level = file_level
        self.label = sluggy(label)
        self.folder = folder or Path("./_logs")

        # ensure folder is created
        try:
            self.folder.mkdir(exist_ok=True, parents=True)
        except PermissionError as err:
            msg_err = (
                f"Impossible to create the logs folder. Does the user '{getuser}' have "
                f"write permissions on: {self.folder}. Trace: {err}"
            )
            logger.error(msg_err)

        # create logger
        self.initial_logger_config()

    def initial_logger_config(self) -> logging.Logger:
        """Configure root logger.

        Returns:
            configured logger
        """
        #  create main logger
        logging.captureWarnings(False)
        logger = logging.getLogger()
        logger.setLevel(min(self.console_level, self.file_level))

        # create console handler - seems to be ignored by click
        log_console_handler = logging.StreamHandler()
        log_console_handler.setLevel(self.console_level)

        # create file handler
        logs_filepath = self.folder.joinpath(f"{self.label}.log")
        log_file_handler = RotatingFileHandler(
            backupCount=10,
            delay=10,
            encoding="UTF-8",
            filename=logs_filepath,
            maxBytes=3000000,
            mode="a",
        )

        # force new file by execution
        if logs_filepath.is_file():
            log_file_handler.doRollover()

        log_file_handler.setLevel(self.file_level)

        # apply format
        log_file_handler.setFormatter(self.LOG_FORMAT)

        # add only file handler to the logger, to avoid duplicated messages
        # logger.addHandler(log_console_handler)
        logger.addHandler(log_file_handler)

        return logger

    def headers(self):
        """Log basic information before other message."""
        # initialize the log
        logger.info(f"{'='*10} {package_name} - Version {__version__} {'='*10}")
        logger.info(f"Operating System: {opersys()}")
        logger.info(f"Architecture: {architecture()[0]}")
        logger.info(f"Computer: {gethostname()}")
        logger.info(f"Launched by: {getuser()}")
        logger.info(f"OS Domain: {environ.get('userdomain')}")
        logger.info(f"Network proxies detected: {len(getproxies())}")
        logger.info(f"GDAL: {get_gdal_version()}")
        logger.info(f"PROJ: {get_proj_version()}")
