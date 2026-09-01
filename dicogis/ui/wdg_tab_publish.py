#! python3  # noqa: E265


"""
Name:         TabPublish
Purpose:      Tab to publish previously exported metadata (JSON files) to a
              uData catalog, from DicoGIS Notebook.

Author:       Julien Moura (@geojulien)
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import logging
from os import getenv
from pathlib import Path

# GUI
from PyQt6 import uic
from PyQt6.QtWidgets import QFileDialog, QLineEdit, QWidget

# project
from dicogis.cli.cmd_publish import PublishReport
from dicogis.ui.wdg_scrollable_table import ScrollableTable
from dicogis.utils.check_path import check_path
from dicogis.utils.utils import Utilities


# ##############################################################################
# ############ Globals ############
# #################################

logger = logging.getLogger(__name__)

# ##############################################################################
# ########## Classes ###############
# ##################################


class TabPublish(QWidget):
    """Tab form to publish DicoGIS metadata JSON files to a uData catalog.

    Args:
        QWidget: inherited Qt widget
    """

    def __init__(
        self,
        parent: QWidget | None = None,
    ):
        """Initializes UI tab for uData publication.

        Args:
            parent: Qt parent widget
        """
        super().__init__(parent)
        uic.loadUi(
            Utilities().resolve_internal_path(
                internal_path=Path("ui/wdg_tab_publish.ui")
            ),
            self,
        )

        self.ent_input_folder.setText(getenv("DICOGIS_PUBLISH_INPUT_FOLDER", ""))
        self.btn_browse_input_folder.clicked.connect(self.on_browse_input_folder)

        self.ent_udata_api_url_base.setText(
            getenv("DICOGIS_UDATA_API_URL_BASE", "https://demo.data.gouv.fr/api/")
        )
        self.ent_udata_api_version.setText(getenv("DICOGIS_UDATA_API_VERSION", "1"))
        self.ent_udata_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.ent_udata_api_key.setText(getenv("DICOGIS_UDATA_API_KEY", ""))
        self.ent_udata_organization_id.setText(
            getenv("DICOGIS_UDATA_ORGANIZATION_ID", "")
        )

        self.tab_publish_errors = ScrollableTable(self.FrReport)
        self.tab_publish_errors.table.setHorizontalHeaderLabels(
            [
                self.tr("File"),
                self.tr("Error"),
            ]
        )
        self.FrReport.layout().addWidget(self.tab_publish_errors)

        self.retranslate_ui()

    def on_browse_input_folder(self) -> Path | None:
        """Browse and insert the path of the folder containing JSON metadata files.

        Returns:
            selected folder path or None if something went wrong
        """
        initial_folder = Path(self.ent_input_folder.text() or Path().home())
        try:
            check_path(
                input_path=initial_folder,
                must_be_a_folder=True,
                must_be_a_file=False,
                must_exists=True,
            )
        except Exception as err:
            logger.info(
                f"Initial publish folder ({initial_folder}) is not a valid existing "
                f"folder. Fallback to user's home. Trace: {err}"
            )
            initial_folder = Path().home()

        foldername = QFileDialog.getExistingDirectory(
            self,
            self.tr("Pick the folder containing JSON metadata"),
            str(initial_folder),
        )

        if not foldername:
            return None

        self.ent_input_folder.setText(foldername)
        return Path(foldername)

    def clear_report(self) -> None:
        """Reset the publication report (summary + errors table)."""
        self.lbl_publish_summary.setText("")
        self.tab_publish_errors.table.setRowCount(0)

    def show_report(self, report: PublishReport) -> None:
        """Display a publish_metadata_folder() report in the tab.

        Args:
            report: outcome of the publication run.
        """
        self.lbl_publish_summary.setText(
            self.tr(
                "{published} published - {ignored} ignored - {failed} failed"
            ).format(
                published=report.published, ignored=report.ignored, failed=report.failed
            )
        )
        for error_message in report.errors:
            self.tab_publish_errors.add_row("", error_message)

    # -- Accessors used by the main window / OptionsManager --------------------------

    def get_input_folder(self) -> str:
        """Return the currently entered JSON metadata folder path."""
        return self.ent_input_folder.text()

    def set_input_folder(self, folder_path: str) -> None:
        """Set the JSON metadata folder path."""
        self.ent_input_folder.setText(folder_path)

    def get_udata_api_key(self) -> str:
        """Return the currently entered uData API key."""
        return self.ent_udata_api_key.text()

    def get_udata_api_url_base(self) -> str:
        """Return the currently entered uData API base URL."""
        return self.ent_udata_api_url_base.text()

    def get_udata_api_version(self) -> str:
        """Return the currently entered uData API version."""
        return self.ent_udata_api_version.text()

    def get_udata_organization_id(self) -> str | None:
        """Return the currently entered uData organization ID, or None if empty."""
        return self.ent_udata_organization_id.text() or None

    def get_publish_options(self) -> dict:
        """Return publish options as a dict. The API key is not included: it is not
        persisted to options.ini for security reasons.
        """
        return {
            "input_folder": self.get_input_folder(),
            "udata_api_url_base": self.get_udata_api_url_base(),
            "udata_api_version": self.get_udata_api_version(),
            "udata_organization_id": self.get_udata_organization_id() or "",
        }

    def set_publish_options(self, values: dict) -> None:
        """Apply publish options from a dict."""
        if input_folder := values.get("input_folder"):
            self.set_input_folder(input_folder)
        if api_url_base := values.get("udata_api_url_base"):
            self.ent_udata_api_url_base.setText(api_url_base)
        if api_version := values.get("udata_api_version"):
            self.ent_udata_api_version.setText(api_version)
        if organization_id := values.get("udata_organization_id"):
            self.ent_udata_organization_id.setText(organization_id)

    def retranslate_ui(self) -> None:
        """Update widgets texts for the currently active language."""
        self.FrSource.setTitle(self.tr("Metadata source"))
        self.lb_input_folder.setText(self.tr("JSON metadata folder: "))
        self.btn_browse_input_folder.setText(self.tr("Browse"))
        self.FrCatalog.setTitle(self.tr("uData catalog"))
        self.lb_udata_api_url_base.setText(self.tr("API URL:"))
        self.lb_udata_api_version.setText(self.tr("API version:"))
        self.lb_udata_api_key.setText(self.tr("API key:"))
        self.lb_udata_organization_id.setText(self.tr("Organization ID (optional):"))
        self.FrReport.setTitle(self.tr("Publication report"))
        self.tab_publish_errors.table.setHorizontalHeaderLabels(
            [
                self.tr("File"),
                self.tr("Error"),
            ]
        )


# #############################################################################
# ##### Stand alone program ########
# ##################################

if __name__ == "__main__":
    """To test"""
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    widget = TabPublish()
    widget.show()
    sys.exit(app.exec())
