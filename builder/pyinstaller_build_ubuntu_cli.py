#! python3  # noqa: E265

"""
    Launch PyInstaller using a Python script.
"""

# #############################################################################
# ########## Libraries #############
# ##################################

import platform
import sys

# Standard library
from os import getenv
from pathlib import Path

# 3rd party
import distro
import PyInstaller.__main__

# package
sys.path.insert(0, str(Path(".").resolve()))
from dicogis import __about__  # noqa: E402

# #############################################################################
# ########### MAIN #################
# ##################################
package_folder = Path("dicogis")

PyInstaller.__main__.run(
    [
        "--add-binary={}:bin/img/".format((package_folder / "bin/img/").resolve()),
        "--add-data={}:locale/".format((package_folder / "locale/").resolve()),
        "--add-data=options_TPL.ini:.",
        "--add-data=LICENSE:.",
        "--add-data=README.md:.",
        "--collect-submodules=shellingham",
        "--console",
        "--log-level={}".format(getenv("PYINSTALLER_LOG_LEVEL", "WARN")),
        "--name={}-cli_{}_{}{}_{}_Python{}".format(
            __about__.__title_clean__,
            __about__.__version__,
            distro.id(),
            distro.version(),
            platform.architecture()[0],
            platform.python_version(),
        ).replace(".", "-"),
        "--noconfirm",
        "--onefile",
        str(package_folder.joinpath("cli/main.py")),
    ]
)
