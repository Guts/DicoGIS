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
from dicogis.utils.texts import TextsManager
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
        localized_strings: dict | None = None,
    ) -> None:
        """Initialize the database connection dialog.

        Args:
            parent: the parent widget.
            localized_strings: translated strings. Defaults to None.
        """
        super().__init__(parent)
        uic.loadUi(
            Utilities().resolve_internal_path(
                internal_path=Path("ui/dialogs/dlg_database_connection.ui")
            ),
            self,
        )
        self.setModal(True)

        # handle empty localized strings
        self.localized_strings = localized_strings
        if self.localized_strings is None:
            self.localized_strings = TextsManager().load_texts()

        self.retranslate_ui(self.localized_strings)

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

    def retranslate_ui(self, localized_strings: dict) -> None:
        """Update the dialog's texts with the given localized strings.

        Args:
            localized_strings: translated strings.
        """
        self.localized_strings = localized_strings
        self.setWindowTitle(
            localized_strings.get(
                "gui_database_connection_form_title", "Add a new database connection"
            )
        )
        self.lbl_service_name.setText(
            localized_strings.get("gui_database_service_name", "Service name:")
        )
        self.lbl_host.setText(localized_strings.get("gui_host", "Host:"))
        self.lbl_port.setText(localized_strings.get("gui_port", "Port:"))
        self.lbl_db_name.setText(localized_strings.get("gui_db", "Database:"))
        self.lbl_user.setText(localized_strings.get("gui_user", "Username:"))
        self.lbl_password.setText(localized_strings.get("gui_mdp", "Password:"))


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
