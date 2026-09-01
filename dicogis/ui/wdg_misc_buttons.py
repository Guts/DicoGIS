#! python3  # noqa: E265

"""
Name:         MiscButtons
Purpose:      Miscellaneous widgets for DicoGIS Notebook.

Author:       Julien Moura (@geojulien)
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import logging
from pathlib import Path
from webbrowser import open_new_tab

# 3rd party
from PyQt6 import uic
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QWidget
from typer import get_app_dir, launch

# package
from dicogis.__about__ import (
    __copyright__,
    __email__,
    __title__,
    __uri__,
    __uri_homepage__,
)
from dicogis.utils.utils import Utilities


# ##############################################################################
# ############ Globals ############
# #################################

app_dir = get_app_dir(app_name=__title__, force_posix=True)
logger = logging.getLogger(__name__)

# ##############################################################################
# ########## Classes ###############
# ##################################


class MiscButtons(QWidget):
    """Miscellaneous buttons.

    Args:
        QWidget: inherited Qt widget
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        images_folder: str | Path = "bin/img",
    ):
        """UI frame on the application left side frame with logo and miscellaneous buttons.

        Args:
            parent: Qt parent widget
            images_folder: folder where images are stored. Defaults to "bin/img".
        """
        super().__init__(parent)
        self.dicogis_utils = Utilities()
        uic.loadUi(
            self.dicogis_utils.resolve_internal_path(
                internal_path=Path("ui/wdg_misc_buttons.ui")
            ),
            self,
        )

        self.dir_imgs = self.dicogis_utils.resolve_internal_path(
            internal_path=images_folder
        )

        # logo
        pixmap = QPixmap(str(self.dir_imgs.joinpath("DicoGIS_logo_200px.png")))
        self.lbl_logo.setPixmap(pixmap)

        # credits
        self.btn_credits.setText(__copyright__)
        self.btn_credits.clicked.connect(lambda: open_new_tab(__uri__))

        # contact
        mailto = f"mailto:{__email__}?subject=[{__title__}]%20Question"
        self.btn_contact.clicked.connect(lambda: open_new_tab(mailto))

        # source
        url_src = f"{__uri__}issues"
        self.btn_src.clicked.connect(lambda: open_new_tab(url_src))

        # documentation
        self.btn_doc.setText(self.tr("Documentation"))
        self.btn_doc.clicked.connect(lambda: open_new_tab(__uri_homepage__))

        # sponsor
        self.btn_support.setText(self.tr("Fund & Support"))
        self.btn_support.clicked.connect(
            lambda: open_new_tab(f"{__uri_homepage__}misc/funding.html")
        )

        # application folder
        self.btn_app_dir.setText(self.tr("Application folder"))
        self.btn_app_dir.clicked.connect(lambda: launch(app_dir))


# #############################################################################
# ##### Stand alone program ########
# ##################################

if __name__ == "__main__":
    """To test"""
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    widget = MiscButtons()
    widget.show()
    sys.exit(app.exec())
