#! python3  # noqa: E265


"""
Name:         DatabaseConnectionDialog
Purpose:      Modal dialog to create a new database connection.

Author:       Julien Moura (@geojulien)
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import logging
from pathlib import Path

# 3rd party
from PyQt6 import uic
from PyQt6.QtWidgets import QDialog, QWidget

# project
from dicogis.models.database_connection import DatabaseConnection
from dicogis.utils.utils import Utilities

# ##############################################################################
# ############ Globals ############
# #################################

logger = logging.getLogger(__name__)

# ##############################################################################
# ########## Classes ###############
# ##################################


class DatabaseConnectionDialog(QDialog):
    """Modal dialog to create a new database connection."""

    out_database_connection: DatabaseConnection | None = None

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize the database connection dialog.

        Args:
            parent: the parent widget.
        """
        super().__init__(parent)
        uic.loadUi(
            Utilities().resolve_internal_path(
                internal_path=Path("ui/dialogs/dlg_database_connection.ui")
            ),
            self,
        )
        self.setModal(True)

        self.retranslate_ui()

        self.buttons.accepted.connect(self._on_submit)
        self.buttons.rejected.connect(self.reject)

    def _on_submit(self) -> None:
        """Collect the data from the entries and accept the dialog."""
        self.out_database_connection = DatabaseConnection(
            database_name=self.ent_db_name.text(),
            service_name=self.ent_service_name.text(),
            host=self.ent_host.text(),
            port=self.ent_port.value(),
            user_name=self.ent_user.text(),
            user_password=self.ent_password.text(),
        )
        self.accept()

    def retranslate_ui(self) -> None:
        """Update the dialog's texts for the currently active language."""
        self.setWindowTitle(self.tr("Add a new database connection"))
        self.lbl_service_name.setText(self.tr("Service name:"))
        self.lbl_host.setText(self.tr("Host: "))
        self.lbl_port.setText(self.tr("Port: "))
        self.lbl_db_name.setText(self.tr("Database: "))
        self.lbl_user.setText(self.tr("User: "))
        self.lbl_password.setText(self.tr("Password: "))


# #############################################################################
# ##### Stand alone program ########
# ##################################

if __name__ == "__main__":
    """To test"""
    import sys

    from PyQt6.QtWidgets import QApplication

    logging.basicConfig(level=logging.DEBUG)

    app = QApplication(sys.argv)
    dialog = DatabaseConnectionDialog()
    dialog.exec()
    print(dialog.out_database_connection)
