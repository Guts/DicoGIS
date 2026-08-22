#! python3  # noqa: E265


"""
Name:         TabDatabase
Purpose:      Tab containing database widgets in DicoGIS Notebook.

Author:       Julien Moura (@geojulien)
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import logging

# 3rd party
import pgserviceparser
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# project
from dicogis.models.database_connection import DatabaseConnection
from dicogis.ui.dialogs.database_connection_dialog import DatabaseConnectionDialog
from dicogis.utils.texts import TextsManager

# ##############################################################################
# ############ Globals ############
# #################################

# LOG
logger = logging.getLogger(__name__)

# ##############################################################################
# ########## Classes ###############
# ##################################


class TabDatabaseServer(QWidget):
    """Tab form for server database connections.

    Args:
        QWidget: inherited Qt widget
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        localized_strings: dict | None = None,
        init_widgets: bool = True,
    ):
        """UI tab for databases initialization.

        Args:
            parent: Qt parent widget
            localized_strings: translated strings. Defaults to None.
            init_widgets: option to create widgets during init or not. Defaults to True.
        """
        super().__init__(parent)

        # attributes
        try:
            self.pg_services_names = pgserviceparser.service_names()
        except pgserviceparser.ServiceFileNotFound as err:
            logger.info(
                f"Unable to find the pg_service.conf file: {err} "
                "Using empty list for pg_services_names.",
            )
            self.pg_services_names = []

        # handle empty localized strings
        self.localized_strings = localized_strings
        if self.localized_strings is None:
            self.localized_strings = TextsManager().load_texts()

        if init_widgets:
            self.create_widgets()

    def create_widgets(self) -> None:
        """Create and layout the widgets for the frame."""
        layout = QVBoxLayout(self)

        # subframe
        self.FrameDatabaseServicePicker = QGroupBox(
            self.localized_strings.get("gui_fr2", "PostGIS"), self
        )
        form_layout = QFormLayout()

        # Form widgets
        self.ddl_pg_services = QComboBox(self.FrameDatabaseServicePicker)
        self.ddl_pg_services.addItems(self.pg_services_names)

        self.caz_pg_views = QCheckBox(
            self.localized_strings.get("gui_views", "Views enabled"),
            self.FrameDatabaseServicePicker,
        )

        # Button to open modal dialog
        self.open_form_button = QPushButton(
            self.localized_strings.get("gui_database_form", "+"),
            self.FrameDatabaseServicePicker,
        )
        self.open_form_button.clicked.connect(self.open_form)

        self.lb_pg_services = QLabel(
            self.localized_strings.get("gui_pg_service", "PG service:"),
            self.FrameDatabaseServicePicker,
        )

        form_layout.addRow(self.lb_pg_services, self.ddl_pg_services)
        form_layout.addRow(self.open_form_button)
        form_layout.addRow(self.caz_pg_views)

        self.FrameDatabaseServicePicker.setLayout(form_layout)
        layout.addWidget(self.FrameDatabaseServicePicker)
        layout.addStretch(1)

    def open_form(self) -> None:
        """Open the modal dialog for database form."""
        dialog = DatabaseConnectionDialog(self, localized_strings=self.localized_strings)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        if not isinstance(dialog.out_database_connection, DatabaseConnection):
            logger.debug("No database connection created.")
            return

        save_status, log_msg = dialog.out_database_connection.store_in_pgservice_file()
        if save_status:
            logger.info(log_msg)
            self.pg_services_names = pgserviceparser.service_names()
            self.ddl_pg_services.clear()
            self.ddl_pg_services.addItems(self.pg_services_names)
        else:
            logger.error(log_msg, stack_info=True)
            QMessageBox.critical(
                self,
                self.localized_strings.get(
                    "gui_database_save_new_service_error", "+"
                ),
                log_msg,
            )

    # -- Accessors used by OptionsManager -------------------------------------------

    def get_selected_pg_service(self) -> str:
        """Return the currently selected PG service name."""
        return self.ddl_pg_services.currentText()

    def set_selected_pg_service(self, service_name: str) -> None:
        """Select a PG service by name if it exists in the combobox."""
        if service_name in self.pg_services_names:
            self.ddl_pg_services.setCurrentText(service_name)

    def get_views_enabled(self) -> bool:
        """Return whether PostGIS views are enabled."""
        return self.caz_pg_views.isChecked()

    def set_views_enabled(self, value: bool) -> None:
        """Set whether PostGIS views are enabled."""
        self.caz_pg_views.setChecked(bool(value))

    def retranslate_ui(self, localized_strings: dict) -> None:
        """Update widgets texts with the given localized strings.

        Args:
            localized_strings: translated strings.
        """
        self.localized_strings = localized_strings
        self.FrameDatabaseServicePicker.setTitle(
            localized_strings.get("gui_fr2", "PostGIS")
        )
        self.caz_pg_views.setText(
            localized_strings.get("gui_views", "Views enabled")
        )
        self.open_form_button.setText(
            localized_strings.get("gui_database_form", "+")
        )
        self.lb_pg_services.setText(
            localized_strings.get("gui_pg_service", "PG service:")
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
    widget = TabDatabaseServer()
    widget.show()
    sys.exit(app.exec())
