#! python3  # noqa: E265

"""
    Log management.

    Author: Julien Moura

    See: https://docs.python.org/fr/3/howto/logging.html
"""

# #############################################################################
# ########## Libraries #############
# ##################################

import getpass

# Standard library
import gettext
import logging
from logging.handlers import RotatingFileHandler
from os import environ
from pathlib import Path
from platform import architecture
from platform import platform as opersys
from socket import gethostname
from urllib.request import getproxies

# modules
from dicogis.__about__ import __title_clean__ as package_name
from dicogis.__about__ import __version__

# #############################################################################
# ########## Globals ###############
# ##################################

_ = gettext.gettext  # i18n
logger = logging.getLogger(__name__)  # logs


# #############################################################################
# ########## Classes ###############
# ##################################


class LogManager:
    """Manage logs: configuration, parsing, etc."""

    LOG_FORMAT = logging.Formatter(
        "%(asctime)s || %(levelname)s "
        "|| %(module)s - %(lineno)d ||"
        " %(funcName)s || %(message)s"
    )

    def __init__(
        self,
        console_level: int = logging.WARNING,
        file_level: int = logging.INFO,
        label: str = package_name,
        folder: Path = Path("./_logs"),
    ):
        """Instanciation method."""
        # store parameters as attributes
        self.console_level = console_level
        self.file_level = file_level
        self.label = "".join(e for e in label if e.isalnum())

        # ensure folder is created
        try:
            folder.mkdir(exist_ok=True, parents=True)
        except PermissionError as err:
            msg_err = _(
                "Impossible to create the logs folder. Does the user '{}' ({}) have "
                "write permissions on: {}. Trace: {}"
            ).format(environ.get("userdomain"), getpass.getuser(), folder, err)
            logger.error(msg_err)
        self.folder = folder

        # create logger
        self.initial_logger_config()

    def initial_logger_config(self) -> logging.Logger:
        """Configure root logger. \
        BE CAREFUL: it depends a lot of how click implemented logging facilities. \
        So, sadly, every option is not available.

        :return: configured logger
        :rtype: logging.Logger
        """
        #  create main logger
        logging.captureWarnings(False)
        logger = logging.getLogger()
        logger.setLevel(self.console_level)

        # create console handler - seems to be ignored by click
        log_console_handler = logging.StreamHandler()
        log_console_handler.setLevel(self.console_level)

        # create file handler
        log_file_handler = RotatingFileHandler(
            filename=self.folder / "{}.log".format(self.label),
            mode="a",
            maxBytes=3000000,
            backupCount=10,
            encoding="UTF-8",
        )
        log_file_handler.setLevel(self.file_level)

        # apply format
        log_file_handler.setFormatter(self.LOG_FORMAT)

        # add only file handler to the logger, to avoid duplicated messages
        # logger.addHandler(log_console_handler)
        logger.addHandler(log_file_handler)

        return logger

    def headers(self):
        """Basic information to log before other message."""
        # initialize the log
        logger.info(
            "\t ========== {} - Version {} ==========".format(package_name, __version__)
        )
        logger.info(_("Operating System: {}").format(opersys()))
        logger.info(_("Architecture: {}").format(architecture()[0]))
        logger.info(_("Computer: {}").format(gethostname()))
        logger.info(_("Launched by: {}").format(getpass.getuser()))
        logger.info(_("OS Domain: {}").format(environ.get("userdomain")))
        logger.info(_("Network proxies detected: {}").format(len(getproxies())))


# #############################################################################
# ##### Main #######################
# ##################################
if __name__ == "__main__":
    pass
