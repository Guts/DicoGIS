#! python3  # noqa: E265


"""
Name:         TabCredits
Purpose:      Tab containing credits and license informations in DicoGIS Notebook.

Author:       Julien Moura (@geojulien)
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import logging
import platform
from pathlib import Path

# 3rd party
from lxml import __version__ as lxml_version
from numpy import __version__ as numpy_version
from openpyxl import __version__ as openpyxl_version
from PyQt6 import uic
from PyQt6.QtCore import PYQT_VERSION_STR, qVersion
from PyQt6.QtWidgets import QLabel, QWidget

# project
from dicogis.utils.environment import get_gdal_version, get_proj_version
from dicogis.utils.utils import Utilities

# ##############################################################################
# ############ Globals ############
# #################################

# LOG
logger = logging.getLogger(__name__)

# ##############################################################################
# ########## Classes ###############
# ##################################


class TabCredits(QWidget):
    """Tab displaying project credits. Displayed during data processing.

    Args:
        QWidget: inherited Qt widget
    """

    def __init__(self, parent: QWidget | None = None):
        """UI tab for credits/dependencies display.

        Args:
            parent: Qt parent widget
        """
        super().__init__(parent)
        uic.loadUi(
            Utilities().resolve_internal_path(
                internal_path=Path("ui/wdg_tab_credits.ui")
            ),
            self,
        )

        rows = [
            ("GDAL", get_gdal_version()),
            ("PROJ", get_proj_version()),
            ("LXML", lxml_version),
            ("Numpy", numpy_version),
            ("OpenPyXL", openpyxl_version),
            ("Qt (PyQt6)", f"{PYQT_VERSION_STR} (Qt {qVersion()})"),
            ("Python", platform.python_version()),
        ]

        for row_index, (name, value) in enumerate(rows):
            self.gridLayout.addWidget(QLabel(name, self), row_index, 0)
            self.gridLayout.addWidget(QLabel(str(value), self), row_index, 1)


# #############################################################################
# ##### Stand alone program ########
# ##################################
if __name__ == "__main__":
    """To test"""
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    widget = TabCredits()
    widget.show()
    sys.exit(app.exec())
