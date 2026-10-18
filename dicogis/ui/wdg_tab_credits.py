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

# project
from dicogis.ui.qt_compat import uic
from dicogis.ui.qt_compat.QtCore import PYQT_VERSION_STR, qVersion
from dicogis.ui.qt_compat.QtWidgets import QWidget
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

        self.lbl_gdal_version.setText(str(get_gdal_version()))
        self.lbl_proj_version.setText(str(get_proj_version()))
        self.lbl_lxml_version.setText(lxml_version)
        self.lbl_numpy_version.setText(numpy_version)
        self.lbl_openpyxl_version.setText(openpyxl_version)
        self.lbl_qt_version.setText(f"{PYQT_VERSION_STR} (Qt {qVersion()})")
        self.lbl_python_version.setText(platform.python_version())


# #############################################################################
# ##### Stand alone program ########
# ##################################
if __name__ == "__main__":
    """To test"""
    import sys

    from dicogis.ui.qt_compat.QtWidgets import QApplication

    app = QApplication(sys.argv)
    widget = TabCredits()
    widget.show()
    sys.exit(app.exec())
