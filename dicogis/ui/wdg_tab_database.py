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
from pathlib import Path

# 3rd party
import pgserviceparser
from PyQt6 import uic
from PyQt6.QtWidgets import QDialog, QMessageBox, QWidget

# project
from dicogis.models.database_connection import DatabaseConnection
from dicogis.ui.dialogs.dlg_database_connection import DatabaseConnectionDialog
from dicogis.utils.utils import Utilities


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
    ):
        """UI tab for databases initialization.

        Args:
            parent: Qt parent widget
        """
        super().__init__(parent)
        uic.loadUi(
            Utilities().resolve_internal_path(
                internal_path=Path("ui/wdg_tab_database.ui")
            ),
            self,
        )

        # attributes
        try:
            self.pg_services_names = pgserviceparser.service_names()
        except pgserviceparser.ServiceFileNotFound as err:
            logger.info(
                f"Unable to find the pg_service.conf file: {err} "
                "Using empty list for pg_services_names.",
            )
            self.pg_services_names = []

        self.ddl_pg_services.addItems(self.pg_services_names)
        self.open_form_button.clicked.connect(self.open_form)

        self.retranslate_ui()

    def open_form(self) -> None:
        """Open the modal dialog for database form."""
        dialog = DatabaseConnectionDialog(self)
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
                self.tr("+"),
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

    def retranslate_ui(self) -> None:
        """Update widgets texts for the currently active language."""
        self.FrameDatabaseServicePicker.setTitle(
            self.tr(" Database connection settings ")
        )
        self.caz_pg_views.setText(self.tr("See views? "))
        self.open_form_button.setText(self.tr("+"))
        self.lb_pg_services.setText(self.tr("PG service:"))


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
