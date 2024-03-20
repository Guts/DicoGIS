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
from logging.handlers import RotatingFileHandler
from os import getenv
from sys import platform as opersys

# GUI
from tkinter import TkVersion

# Project
from dicogis.ui.main_windows import DicoGIS

# ##############################################################################
# ############ Globals ############
# #################################


logger = logging.getLogger("DicoGIS")

# ##############################################################################
# ############ Functions ###########
# ##################################


def dicogis_gui():
    """Launch DicoGIS GUI."""
    # LOG
    logging.captureWarnings(True)
    logger.setLevel(logging.DEBUG)  # all errors will be get
    log_form = logging.Formatter(
        "%(asctime)s || %(levelname)s "
        "|| %(module)s - %(lineno)d ||"
        " %(funcName)s || %(message)s"
    )
    logfile = RotatingFileHandler("LOG_DicoGIS.log", "a", 5000000, 1)
    logfile.setLevel(logging.DEBUG)
    logfile.setFormatter(log_form)
    logger.addHandler(logfile)

    # 3rd party
    # condition import
    if opersys == "linux":
        import distro

    # check Tk version
    logger.info(f"{TkVersion=}")
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
            theme = "yaru"
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
