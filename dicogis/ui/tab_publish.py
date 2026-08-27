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
from PyQt6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# project
from dicogis.cli.cmd_publish import PublishReport
from dicogis.ui.scrollable_table import ScrollableTable
from dicogis.utils.check_path import check_path
from dicogis.utils.texts import TextsManager

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
        localized_strings: dict | None = None,
        init_widgets: bool = True,
    ):
        """Initializes UI tab for uData publication.

        Args:
            parent: Qt parent widget
            localized_strings: translated strings. Defaults to None.
            init_widgets: option to create widgets during init or not. Defaults to True.
        """
        super().__init__(parent)

        # handle empty localized strings
        self.localized_strings = localized_strings
        if self.localized_strings is None:
            self.localized_strings = TextsManager().load_texts()

        if init_widgets:
            self.create_widgets()

    def create_widgets(self) -> None:
        """Create and layout the widgets for the frame."""
        layout = QVBoxLayout(self)

        # -- SOURCE -----------------------------------------------------------------
        self.FrSource = QGroupBox(
            self.localized_strings.get("gui_publish_source", "Metadata source"), self
        )
        source_layout = QGridLayout()

        self.lb_input_folder = QLabel(
            self.localized_strings.get(
                "gui_publish_input_folder", "JSON metadata folder: "
            ),
            self.FrSource,
        )
        self.ent_input_folder = QLineEdit(self.FrSource)
        self.ent_input_folder.setText(getenv("DICOGIS_PUBLISH_INPUT_FOLDER", ""))
        self.btn_browse_input_folder = QPushButton(
            self.localized_strings.get("gui_choix", "Browse"), self.FrSource
        )
        self.btn_browse_input_folder.clicked.connect(self.on_browse_input_folder)

        source_layout.addWidget(self.lb_input_folder, 0, 0)
        source_layout.addWidget(self.ent_input_folder, 0, 1)
        source_layout.addWidget(self.btn_browse_input_folder, 0, 2)
        self.FrSource.setLayout(source_layout)

        # -- UDATA CATALOG ------------------------------------------------------------
        self.FrCatalog = QGroupBox(
            self.localized_strings.get("gui_publish_catalog", "uData catalog"), self
        )
        catalog_layout = QFormLayout()

        self.ent_udata_api_url_base = QLineEdit(self.FrCatalog)
        self.ent_udata_api_url_base.setText(
            getenv("DICOGIS_UDATA_API_URL_BASE", "https://demo.data.gouv.fr/api/")
        )
        self.ent_udata_api_version = QLineEdit(self.FrCatalog)
        self.ent_udata_api_version.setText(getenv("DICOGIS_UDATA_API_VERSION", "1"))
        self.ent_udata_api_key = QLineEdit(self.FrCatalog)
        self.ent_udata_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.ent_udata_api_key.setText(getenv("DICOGIS_UDATA_API_KEY", ""))
        self.ent_udata_organization_id = QLineEdit(self.FrCatalog)
        self.ent_udata_organization_id.setText(
            getenv("DICOGIS_UDATA_ORGANIZATION_ID", "")
        )

        self.lb_udata_api_url_base = QLabel(
            self.localized_strings.get("gui_publish_api_url", "API URL:"),
            self.FrCatalog,
        )
        self.lb_udata_api_version = QLabel(
            self.localized_strings.get("gui_publish_api_version", "API version:"),
            self.FrCatalog,
        )
        self.lb_udata_api_key = QLabel(
            self.localized_strings.get("gui_publish_api_key", "API key:"),
            self.FrCatalog,
        )
        self.lb_udata_organization_id = QLabel(
            self.localized_strings.get(
                "gui_publish_organization_id", "Organization ID (optional):"
            ),
            self.FrCatalog,
        )

        catalog_layout.addRow(self.lb_udata_api_url_base, self.ent_udata_api_url_base)
        catalog_layout.addRow(self.lb_udata_api_version, self.ent_udata_api_version)
        catalog_layout.addRow(self.lb_udata_api_key, self.ent_udata_api_key)
        catalog_layout.addRow(
            self.lb_udata_organization_id, self.ent_udata_organization_id
        )
        self.FrCatalog.setLayout(catalog_layout)

        # -- REPORT ---------------------------------------------------------------
        self.FrReport = QGroupBox(
            self.localized_strings.get("gui_publish_report", "Publication report"),
            self,
        )
        report_layout = QVBoxLayout()

        self.lbl_publish_summary = QLabel("", self.FrReport)
        self.tab_publish_errors = ScrollableTable(
            self.FrReport, localized_strings=self.localized_strings
        )
        self.tab_publish_errors.table.setHorizontalHeaderLabels(
            [
                self.localized_strings.get("gui_publish_report_file", "File"),
                self.localized_strings.get("gui_publish_report_error", "Error"),
            ]
        )

        report_layout.addWidget(self.lbl_publish_summary)
        report_layout.addWidget(self.tab_publish_errors)
        self.FrReport.setLayout(report_layout)

        layout.addWidget(self.FrSource)
        layout.addWidget(self.FrCatalog)
        layout.addWidget(self.FrReport)

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
            self.localized_strings.get(
                "gui_publish_pick_folder", "Pick the folder containing JSON metadata"
            ),
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
            self.localized_strings.get(
                "gui_publish_summary",
                "{published} published - {ignored} ignored - {failed} failed",
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

    def retranslate_ui(self, localized_strings: dict) -> None:
        """Update widgets texts with the given localized strings.

        Args:
            localized_strings: translated strings.
        """
        self.localized_strings = localized_strings
        self.FrSource.setTitle(
            localized_strings.get("gui_publish_source", "Metadata source")
        )
        self.lb_input_folder.setText(
            localized_strings.get("gui_publish_input_folder", "JSON metadata folder: ")
        )
        self.btn_browse_input_folder.setText(
            localized_strings.get("gui_choix", "Browse")
        )
        self.FrCatalog.setTitle(
            localized_strings.get("gui_publish_catalog", "uData catalog")
        )
        self.lb_udata_api_url_base.setText(
            localized_strings.get("gui_publish_api_url", "API URL:")
        )
        self.lb_udata_api_version.setText(
            localized_strings.get("gui_publish_api_version", "API version:")
        )
        self.lb_udata_api_key.setText(
            localized_strings.get("gui_publish_api_key", "API key:")
        )
        self.lb_udata_organization_id.setText(
            localized_strings.get(
                "gui_publish_organization_id", "Organization ID (optional):"
            )
        )
        self.FrReport.setTitle(
            localized_strings.get("gui_publish_report", "Publication report")
        )
        self.tab_publish_errors.table.setHorizontalHeaderLabels(
            [
                localized_strings.get("gui_publish_report_file", "File"),
                localized_strings.get("gui_publish_report_error", "Error"),
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
