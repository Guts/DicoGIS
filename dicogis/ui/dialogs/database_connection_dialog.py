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

# 3rd party
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QWidget,
)

# project
from dicogis.models.database_connection import DatabaseConnection
from dicogis.utils.texts import TextsManager

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
        init_widgets: bool = True,
    ) -> None:
        """Initialize the database connection dialog.

        Args:
            parent: the parent widget.
            localized_strings: translated strings. Defaults to None.
            init_widgets: option to create widgets during init or not. Defaults to True.
        """
        super().__init__(parent)
        self.setModal(True)

        # handle empty localized strings
        self.localized_strings = localized_strings
        if self.localized_strings is None:
            self.localized_strings = TextsManager().load_texts()

        self.setWindowTitle(
            self.localized_strings.get(
                "gui_database_connection_form_title", "Add a new database connection"
            )
        )

        if init_widgets:
            self.create_widgets()

    def create_widgets(self) -> None:
        """Create and layout the widgets."""
        layout = QFormLayout(self)

        self.ent_service_name = QLineEdit(self)
        self.ent_host = QLineEdit(self)
        self.ent_port = QSpinBox(self)
        self.ent_port.setRange(1, 65535)
        self.ent_port.setValue(5432)
        self.ent_db_name = QLineEdit(self)
        self.ent_user = QLineEdit(self)
        self.ent_password = QLineEdit(self)
        self.ent_password.setEchoMode(QLineEdit.EchoMode.Password)

        layout.addRow(
            self.localized_strings.get("gui_database_service_name", "Service name:"),
            self.ent_service_name,
        )
        layout.addRow(self.localized_strings.get("gui_host", "Host:"), self.ent_host)
        layout.addRow(self.localized_strings.get("gui_port", "Port:"), self.ent_port)
        layout.addRow(
            self.localized_strings.get("gui_db", "Database:"), self.ent_db_name
        )
        layout.addRow(
            self.localized_strings.get("gui_user", "Username:"), self.ent_user
        )
        layout.addRow(
            self.localized_strings.get("gui_mdp", "Password:"), self.ent_password
        )

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        buttons.accepted.connect(self._on_submit)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

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
        """Update the dialog's title with the given localized strings.

        Args:
            localized_strings: translated strings.
        """
        self.localized_strings = localized_strings
        self.setWindowTitle(
            localized_strings.get(
                "gui_database_connection_form_title", "Add a new database connection"
            )
        )


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
