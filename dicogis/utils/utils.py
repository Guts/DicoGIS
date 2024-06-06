#! python3  # noqa: E265


# ############################################################################
# ######## Libraries #############
# ################################

from __future__ import annotations

# Standard library
import logging
import sys
from importlib import resources
from pathlib import Path
from sys import platform as opersys
from tkinter import ACTIVE, DISABLED

# Imports depending on operating system
if opersys == "win32":
    """windows"""


# package
from dicogis.__about__ import __package_name__

# ##############################################################################
# ############ Globals ############
# #################################

# LOG
logger = logging.getLogger(__name__)

# ############################################################################
# ######### Classes #############
# ###############################


class Utilities:
    """DicoGIS specific utilities."""

    @classmethod
    def resolve_internal_path(cls, internal_path: Path) -> Path:
        """Determine the path to internal resources, handling normal Python execution
        and frozen mode (typically PyInstaller).

        Args:
            internal_path (Path): internal path to resolve from dicogis package folder

        Returns:
            Path: resolved path
        """
        # grab locale folder depending if we are in frozen mode (typically PyInstaller)
        # or as "normal" Python
        if not (getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")):
            internal_path = Path(resources.files(__package_name__)).joinpath(
                internal_path
            )
            logger.debug(f"Internal path resolved in Python mode: {internal_path}")
        else:
            internal_path = Path(getattr(sys, "_MEIPASS", sys.executable)).joinpath(
                internal_path
            )
            logger.debug(f"Internal path resolved in packaged mode: {internal_path}")

        return internal_path

    @classmethod
    def ui_switch(cls, cb_value, parent):
        """Change state of  all children widgets within a parent class.

        cb_value=boolean
        parent=Tkinter class with children (Frame, Labelframe, Tk, etc.)
        """
        if cb_value.get():
            for child in parent.winfo_children():
                child.configure(state=ACTIVE)
        else:
            for child in parent.winfo_children():
                child.configure(state=DISABLED)
