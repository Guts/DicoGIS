#! python3  # noqa: E265

"""Per-user application folder, where DicoGIS keeps its settings and logs."""

# ############################################################################
# ########## Libraries #############
# ##################################

# standard lib
import sys
from os import environ
from pathlib import Path

# project
from dicogis.__about__ import __title__


# ############################################################################
# ########## Functions #############
# ##################################


def get_app_dir(app_name: str = __title__) -> Path:
    """Return the per-user application folder.

    Same location as `typer.get_app_dir(app_name, force_posix=True)`, used by
    earlier versions, so existing settings and logs are found again, without
    depending on Typer (absent from QGIS's Python environment):

    - Windows: `%APPDATA%\\<app_name>`, or `~\\<app_name>` if APPDATA is unset
    - elsewhere: `~/.<app_name>`, lowercase, spaces replaced by hyphens

    The folder is not created.

    Args:
        app_name: application name. Defaults to DicoGIS.

    Returns:
        path to the application folder
    """
    if sys.platform.startswith("win"):
        folder = environ.get("APPDATA")
        return Path(folder if folder is not None else Path.home(), app_name)

    return Path.home() / f".{'-'.join(app_name.split()).lower()}"
