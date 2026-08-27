#! python3  # noqa: E265


"""
DicoGIS
Automatize the creation of a dictionnary of geographic data
            contained in a folders structures.
            It produces an Excel output file (.xlsx)

Julien Moura (@geojulien)
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# standard library
import logging
import sys
from configparser import ConfigParser
from os import getenv
from pathlib import Path

# GUI
from PyQt6.QtWidgets import QApplication

# 3rd party
from typer import get_app_dir

# Project
from dicogis.__about__ import __package_name__, __title__
from dicogis.ui.main_windows import DicoGIS
from dicogis.utils.journalizer import LogManager
from dicogis.utils.str2bool import str2bool

# ##############################################################################
# ############ Globals ############
# #################################

app_dir = get_app_dir(app_name=__title__, force_posix=True)
logger = logging.getLogger(__name__)

# ##############################################################################
# ############ Functions ###########
# ##################################


def _get_persisted_option(section: str, option: str) -> str | None:
    """Best-effort read of a value saved by the GUI on a previous run.

    Environment variables take precedence over this at call sites, so this is
    only consulted as a fallback, before the OptionsManager/main window (which
    need a QApplication to already exist) are available.

    Args:
        section: options.ini section name.
        option: options.ini option name.

    Returns:
        the stored value, or None if unset/unreadable.
    """
    config = ConfigParser()
    if not config.read("options.ini"):
        return None
    return config.get(section, option, fallback=None) or None


def dicogis_gui():
    """Launch DicoGIS GUI."""
    debug_enabled = str2bool(
        getenv("DICOGIS_DEBUG") or _get_persisted_option("basics", "debug") or False
    )
    # LOG
    logmngr = LogManager(
        console_level=(logging.DEBUG if debug_enabled else logging.WARNING),
        file_level=(logging.DEBUG if debug_enabled else logging.INFO),
        label=f"{__package_name__}-gui",
        folder=Path(app_dir).joinpath("logs"),
    )
    # add headers
    logmngr.headers()

    # launch the main UI
    try:
        app = QApplication(sys.argv)
        ui_style = getenv("DICOGIS_UI_STYLE") or _get_persisted_option("ui", "style")
        if ui_style:
            app.setStyle(ui_style)
        window = DicoGIS()
    except Exception as err:
        logger.critical(
            "Launching DicoGIS UI failed. Did you install the system "
            f"requirements? Trace: {err}"
        )
        raise (err)

    window.show()
    sys.exit(app.exec())


# ############################################################################
# #### Stand alone program ########
# #################################

if __name__ == "__main__":
    """standalone execution"""
    dicogis_gui()
