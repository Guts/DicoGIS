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
from os import getenv
from pathlib import Path
from sys import platform as opersys

# GUI
from tkinter import TkVersion

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


def dicogis_gui():
    """Launch DicoGIS GUI."""
    # LOG
    logmngr = LogManager(
        console_level=(
            logging.DEBUG
            if str2bool(getenv("DICOGIS_DEBUG", False))
            else logging.WARNING
        ),
        file_level=(
            logging.DEBUG if str2bool(getenv("DICOGIS_DEBUG", False)) else logging.INFO
        ),
        label=f"{__package_name__}-gui",
        folder=Path(app_dir).joinpath("logs"),
    )
    # add headers
    logmngr.headers()

    # 3rd party
    # condition import
    if opersys == "linux":
        import distro

    # check Tk version
    logger.info(f"Tk: {TkVersion}")
    if TkVersion < 8.6:
        logger.critical("DicoGIS requires Tkversion >= 8.6.")
        sys.exit(1)

    # determine theme depending on operating system and distro
    theme = "arc"
    if theme_from_env := getenv("DICOGIS_UI_THEME"):
        theme = theme_from_env
    elif opersys == "darwin":
        theme = "breeze"
    elif opersys == "linux":
        theme = "radiance"
        if distro.name().lower() == "ubuntu":
            theme = "ubuntu"
    elif opersys == "win32":
        theme = "breeze"
    else:
        logger.warning(
            f"Your platform/operating system is not recognized: {opersys}. "
            "It may lead to some strange behavior or buggy events."
        )

    logger.info(f"Used theme: {theme}")

    # launch the main UI
    try:
        app = DicoGIS(theme=theme)
        app.set_theme(theme_name=theme)
    except Exception as err:
        logger.critical(
            "Launching DicoGIS UI failed. Did you install the system "
            f"requirements? Trace: {err}"
        )
        raise (err)

    app.mainloop()


# ############################################################################
# #### Stand alone program ########
# #################################

if __name__ == "__main__":
    """standalone execution"""
    dicogis_gui()
