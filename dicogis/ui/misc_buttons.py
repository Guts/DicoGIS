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
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QGridLayout, QLabel, QPushButton, QWidget
from typer import get_app_dir, launch

# package
from dicogis.__about__ import (
    __copyright__,
    __email__,
    __title__,
    __uri__,
    __uri_homepage__,
)
from dicogis.utils.texts import TextsManager
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
        localized_strings: dict | None = None,
        images_folder: str | Path = "bin/img",
    ):
        """UI frame on the application left side frame with logo and miscellaneous buttons.

        Args:
            parent: Qt parent widget
            localized_strings: translated strings. Defaults to None.
            images_folder: folder where images are stored. Defaults to "bin/img".
        """
        super().__init__(parent)

        self.dicogis_utils = Utilities()
        self.dir_imgs = self.dicogis_utils.resolve_internal_path(
            internal_path=images_folder
        )

        # handle empty localized strings
        self.localized_strings = localized_strings
        if self.localized_strings is None:
            self.localized_strings = TextsManager().load_texts()

        layout = QGridLayout(self)

        # logo
        lbl_logo = QLabel(self)
        pixmap = QPixmap(str(self.dir_imgs.joinpath("DicoGIS_logo_200px.png")))
        lbl_logo.setPixmap(pixmap)
        layout.addWidget(lbl_logo, 0, 0, 1, 2)

        # credits
        self.btn_credits = QPushButton(__copyright__, self)
        self.btn_credits.clicked.connect(lambda: open_new_tab(__uri__))
        layout.addWidget(self.btn_credits, 1, 0, 1, 2)

        # contact
        mailto = f"mailto:{__email__}?subject=[{__title__}]%20Question"
        self.btn_contact = QPushButton("Contact", self)
        self.btn_contact.clicked.connect(lambda: open_new_tab(mailto))

        # source
        url_src = f"{__uri__}issues"
        self.btn_src = QPushButton("Report", self)
        self.btn_src.clicked.connect(lambda: open_new_tab(url_src))

        # documentation
        self.btn_doc = QPushButton(
            self.localized_strings.get("ui_misc_btn_documentation", "Documentation"),
            self,
        )
        self.btn_doc.clicked.connect(lambda: open_new_tab(__uri_homepage__))

        # sponsor
        self.btn_support = QPushButton(
            self.localized_strings.get("ui_misc_btn_support", "Fund & Support"), self
        )
        self.btn_support.clicked.connect(
            lambda: open_new_tab(f"{__uri_homepage__}misc/funding.html")
        )

        # application folder
        self.btn_app_dir = QPushButton(
            self.localized_strings.get("ui_misc_btn_app_dir", "Application folder"),
            self,
        )
        self.btn_app_dir.clicked.connect(lambda: launch(app_dir))

        # griding
        layout.addWidget(self.btn_contact, 2, 0)
        layout.addWidget(self.btn_src, 2, 1)
        layout.addWidget(self.btn_doc, 3, 0)
        layout.addWidget(self.btn_support, 3, 1)
        layout.addWidget(self.btn_app_dir, 4, 0, 1, 2)


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
