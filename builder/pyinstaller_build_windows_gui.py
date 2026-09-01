#! python3

"""
Launch PyInstaller using a Python script.
"""

# #############################################################################
# ########## Libraries #############
# ##################################

import sys

# Standard library
from os import getenv
from pathlib import Path

# 3rd party
import PyInstaller.__main__


# package
sys.path.insert(0, str(Path().resolve()))
from dicogis import __about__


# #############################################################################
# ########### MAIN #################
# ##################################
package_folder = Path("dicogis")

PyInstaller.__main__.run(
    [
        "--add-binary={}:bin/audio/".format(
            package_folder.joinpath("bin/audio/").resolve()
        ),
        "--add-binary={}:bin/img/".format(
            package_folder.joinpath("bin/img/").resolve()
        ),
        "--add-data={};locale/".format((package_folder / "locale/").resolve()),
        "--add-data={};ui/".format((package_folder / "ui/*.ui").resolve()),
        "--add-data={};ui/dialogs/".format(
            (package_folder / "ui/dialogs/*.ui").resolve()
        ),
        "--add-data={};ui/i18n/".format((package_folder / "ui/i18n/*.qm").resolve()),
        "--add-data=options_TPL.ini;.",
        "--add-data=LICENSE;.",
        "--add-data=README.md;.",
        "--collect-data=PyQt6",
        "--icon={}".format((package_folder / "bin/img/DicoGIS.ico").resolve()),
        "--log-level={}".format(getenv("PYINSTALLER_LOG_LEVEL", "WARN")),
        "--manifest={}".format((package_folder / "../builder/manifest.xml").resolve()),
        f"--name={__about__.__title_clean__}-gui",
        "--noconfirm",
        "--noupx",
        "--onefile",
        "--version-file={}".format("version_info.txt"),
        "--windowed",
        str(package_folder.joinpath("ui/main.py")),
    ]
)
