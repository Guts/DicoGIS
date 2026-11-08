#! python3  # noqa: E265


"""
:Name: TabPublish
:Purpose: Tab to publish previously exported metadata to a catalog (uData or
    GeoNetwork), from DicoGIS Notebook.
:Author: Julien Moura (@geojulien)
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import logging
from os import getenv
from pathlib import Path

# project
from dicogis.constants import GeonetworkUpdateModes, PublishTargets
from dicogis.publishing.report import PublishReport
from dicogis.ui.qt_compat import uic
from dicogis.ui.qt_compat.QtWidgets import QFileDialog, QLineEdit, QWidget
from dicogis.utils.check_path import check_path
from dicogis.utils.qgis_runtime import qgis_application_is_running
from dicogis.utils.str2bool import str2bool
from dicogis.utils.utils import Utilities


# ##############################################################################
# ############ Globals ############
# #################################

logger = logging.getLogger(__name__)

# ##############################################################################
# ########## Classes ###############
# ##################################


class TabPublish(QWidget):
    """Tab form to publish DicoGIS metadata files to a catalog.

    Args:
        QWidget: inherited Qt widget
    """

    def __init__(
        self,
        parent: QWidget | None = None,
    ):
        """Initializes UI tab for the publication.

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

        self.lne_input_folder.setText(getenv("DICOGIS_PUBLISH_INPUT_FOLDER", ""))
        self.btn_browse_input_folder.clicked.connect(self.on_browse_input_folder)

        for target in PublishTargets:
            self.cbb_publish_target.addItem(target.value, target.value)
        # pages of stk_publish_target are in the same order as PublishTargets
        self.cbb_publish_target.currentIndexChanged.connect(
            self.stk_publish_target.setCurrentIndex
        )
        self.set_publish_target(
            getenv("DICOGIS_PUBLISH_TARGET", PublishTargets.udata.value)
        )

        self.lne_udata_api_url_base.setText(
            getenv("DICOGIS_UDATA_API_URL_BASE", "https://demo.data.gouv.fr/api/")
        )
        self.lne_udata_api_version.setText(getenv("DICOGIS_UDATA_API_VERSION", "1"))
        self.lne_udata_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.lne_udata_api_key.setText(getenv("DICOGIS_UDATA_API_KEY", ""))
        self.lne_udata_organization_id.setText(
            getenv("DICOGIS_UDATA_ORGANIZATION_ID", "")
        )

        self._init_geonetwork_fields()
        self.retranslate_ui()

    def _init_geonetwork_fields(self) -> None:
        """Fill the GeoNetwork fields with their values from the environment."""
        self.lne_geonetwork_url_base.setText(getenv("DICOGIS_GEONETWORK_URL_BASE", ""))
        self.lne_geonetwork_portal.setText(getenv("DICOGIS_GEONETWORK_PORTAL", "srv"))
        self.lne_geonetwork_username.setText(getenv("DICOGIS_GEONETWORK_USERNAME", ""))
        self.lne_geonetwork_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.lne_geonetwork_password.setText(getenv("DICOGIS_GEONETWORK_PASSWORD", ""))
        self.lne_geonetwork_authcfg.setText(getenv("DICOGIS_GEONETWORK_AUTHCFG", ""))
        self.lne_geonetwork_group.setText(getenv("DICOGIS_GEONETWORK_GROUP", ""))
        self.lne_geonetwork_categories.setText(
            getenv("DICOGIS_GEONETWORK_CATEGORIES", "")
        )
        for update_mode in GeonetworkUpdateModes:
            self.cbb_geonetwork_update_mode.addItem(
                update_mode.value, update_mode.value
            )
        self._set_geonetwork_update_mode(
            getenv(
                "DICOGIS_GEONETWORK_UPDATE_MODE", GeonetworkUpdateModes.overwrite.value
            )
        )
        self.cbx_geonetwork_publish_to_all.setChecked(
            bool(str2bool(getenv("DICOGIS_GEONETWORK_PUBLISH_TO_ALL", "false")))
        )
        self.cbx_geonetwork_reject_if_invalid.setChecked(
            bool(str2bool(getenv("DICOGIS_GEONETWORK_REJECT_IF_INVALID", "false")))
        )

        # an authentication configuration only exists within QGIS
        in_qgis = qgis_application_is_running()
        self.lbl_geonetwork_authcfg.setVisible(in_qgis)
        self.lne_geonetwork_authcfg.setVisible(in_qgis)

    def on_browse_input_folder(self) -> Path | None:
        """Browse and insert the path of the folder containing metadata files.

        Returns:
            selected folder path or None if something went wrong
        """
        initial_folder = Path(self.lne_input_folder.text() or Path().home())
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
            self.tr("Pick the folder containing the metadata"),
            str(initial_folder),
        )

        if not foldername:
            return None

        self.lne_input_folder.setText(foldername)
        return Path(foldername)

    def clear_report(self) -> None:
        """Reset the publication report (summary + details table)."""
        self.lbl_publish_summary.setText("")
        self.wdg_publish_errors.tbw_content.setRowCount(0)

    def show_report(self, report: PublishReport) -> None:
        """Display the report of a publication in the tab.

        Args:
            report: outcome of the publication run.
        """
        summary = self.tr(
            "{published} published - {ignored} ignored - {failed} failed"
        ).format(
            published=report.published, ignored=report.ignored, failed=report.failed
        )
        if report.up_to_date:
            summary += " - " + self.tr("{up_to_date} already complete").format(
                up_to_date=report.up_to_date
            )
        self.lbl_publish_summary.setText(summary)
        for file_name, added_fields in report.added_fields.items():
            self.wdg_publish_errors.add_row(
                file_name,
                self.tr("Added: {fields}").format(fields=", ".join(added_fields)),
            )
        for error_message in report.errors:
            self.wdg_publish_errors.add_row("", error_message)

    # -- Accessors used by the main window / OptionsManager --------------------------

    def get_publish_target(self) -> PublishTargets:
        """Return the kind of catalog to publish to."""
        return PublishTargets(self.cbb_publish_target.currentData())

    def set_publish_target(self, target: str) -> None:
        """Select the kind of catalog to publish to, unknown ones being ignored.

        Args:
            target: value of PublishTargets
        """
        index = self.cbb_publish_target.findData(target.strip().lower())
        if index < 0:
            logger.warning(f"Unsupported publication target: '{target}'.")
            return
        self.cbb_publish_target.setCurrentIndex(index)
        self.stk_publish_target.setCurrentIndex(index)

    def get_input_folder(self) -> str:
        """Return the currently entered metadata folder path."""
        return self.lne_input_folder.text()

    def set_input_folder(self, folder_path: str) -> None:
        """Set the metadata folder path."""
        self.lne_input_folder.setText(folder_path)

    def get_udata_api_key(self) -> str:
        """Return the currently entered uData API key."""
        return self.lne_udata_api_key.text()

    def get_udata_api_url_base(self) -> str:
        """Return the currently entered uData API base URL."""
        return self.lne_udata_api_url_base.text()

    def get_udata_api_version(self) -> str:
        """Return the currently entered uData API version."""
        return self.lne_udata_api_version.text()

    def get_udata_organization_id(self) -> str | None:
        """Return the currently entered uData organization ID, or None if empty."""
        return self.lne_udata_organization_id.text() or None

    def get_geonetwork_url_base(self) -> str:
        """Return the currently entered GeoNetwork URL."""
        return self.lne_geonetwork_url_base.text().strip()

    def get_geonetwork_portal(self) -> str:
        """Return the currently entered GeoNetwork portal, `srv` if empty."""
        return self.lne_geonetwork_portal.text().strip() or "srv"

    def get_geonetwork_username(self) -> str:
        """Return the currently entered GeoNetwork username."""
        return self.lne_geonetwork_username.text().strip()

    def get_geonetwork_password(self) -> str:
        """Return the currently entered GeoNetwork password."""
        return self.lne_geonetwork_password.text()

    def get_geonetwork_authcfg(self) -> str | None:
        """Return the identifier of the QGIS authentication configuration to use.

        Returns:
            identifier, or None if empty or outside QGIS, where it means nothing
        """
        if not qgis_application_is_running():
            return None
        return self.lne_geonetwork_authcfg.text().strip() or None

    def get_geonetwork_group(self) -> str:
        """Return the currently entered GeoNetwork group identifier."""
        return self.lne_geonetwork_group.text().strip()

    def get_geonetwork_categories(self) -> list[str]:
        """Return the currently entered GeoNetwork category identifiers."""
        return [
            category.strip()
            for category in self.lne_geonetwork_categories.text().split(",")
            if category.strip()
        ]

    def get_geonetwork_update_mode(self) -> GeonetworkUpdateModes:
        """Return what to do with a record the catalog already has."""
        return GeonetworkUpdateModes(self.cbb_geonetwork_update_mode.currentData())

    def _set_geonetwork_update_mode(self, update_mode: str) -> None:
        """Select what to do with a record the catalog already has, unknown values
        being ignored.

        Args:
            update_mode: value of GeonetworkUpdateModes
        """
        index = self.cbb_geonetwork_update_mode.findData(update_mode.strip().lower())
        if index < 0:
            logger.warning(f"Unsupported GeoNetwork update mode: '{update_mode}'.")
            return
        self.cbb_geonetwork_update_mode.setCurrentIndex(index)

    def get_publish_options(self) -> dict:
        """Return publish options as a dict. The API key and the password are not
        included: they are not persisted to options.ini for security reasons. The
        identifier of an authentication configuration is only a reference.
        """
        return {
            "input_folder": self.get_input_folder(),
            "publish_target": self.get_publish_target().value,
            "udata_api_url_base": self.get_udata_api_url_base(),
            "udata_api_version": self.get_udata_api_version(),
            "udata_organization_id": self.get_udata_organization_id() or "",
            "geonetwork_url_base": self.get_geonetwork_url_base(),
            "geonetwork_portal": self.get_geonetwork_portal(),
            "geonetwork_username": self.get_geonetwork_username(),
            "geonetwork_authcfg": self.lne_geonetwork_authcfg.text().strip(),
            "geonetwork_group": self.get_geonetwork_group(),
            "geonetwork_categories": ",".join(self.get_geonetwork_categories()),
            "geonetwork_update_mode": self.get_geonetwork_update_mode().value,
            "geonetwork_publish_to_all": self.cbx_geonetwork_publish_to_all.isChecked(),
            "geonetwork_reject_if_invalid": (
                self.cbx_geonetwork_reject_if_invalid.isChecked()
            ),
        }

    def set_publish_options(self, values: dict) -> None:
        """Apply publish options from a dict."""
        if input_folder := values.get("input_folder"):
            self.set_input_folder(input_folder)
        if publish_target := values.get("publish_target"):
            self.set_publish_target(publish_target)
        if api_url_base := values.get("udata_api_url_base"):
            self.lne_udata_api_url_base.setText(api_url_base)
        if api_version := values.get("udata_api_version"):
            self.lne_udata_api_version.setText(api_version)
        if organization_id := values.get("udata_organization_id"):
            self.lne_udata_organization_id.setText(organization_id)

        for key, line_edit in (
            ("geonetwork_url_base", self.lne_geonetwork_url_base),
            ("geonetwork_portal", self.lne_geonetwork_portal),
            ("geonetwork_username", self.lne_geonetwork_username),
            ("geonetwork_authcfg", self.lne_geonetwork_authcfg),
            ("geonetwork_group", self.lne_geonetwork_group),
            ("geonetwork_categories", self.lne_geonetwork_categories),
        ):
            if value := values.get(key):
                line_edit.setText(value)
        if update_mode := values.get("geonetwork_update_mode"):
            self._set_geonetwork_update_mode(update_mode)
        for key, checkbox in (
            ("geonetwork_publish_to_all", self.cbx_geonetwork_publish_to_all),
            ("geonetwork_reject_if_invalid", self.cbx_geonetwork_reject_if_invalid),
        ):
            if key in values:
                checkbox.setChecked(bool(str2bool(values[key])))

    def retranslate_ui(self) -> None:
        """Update widgets texts for the currently active language."""
        self.grp_source.setTitle(self.tr("Metadata source"))
        self.lbl_publish_target.setText(self.tr("Catalog type:"))
        self.cbb_publish_target.setItemText(
            self.cbb_publish_target.findData(PublishTargets.udata.value),
            self.tr("uData (JSON files for uData)"),
        )
        self.cbb_publish_target.setItemText(
            self.cbb_publish_target.findData(PublishTargets.geonetwork.value),
            self.tr("GeoNetwork (ISO 19139 XML files)"),
        )
        self.lbl_input_folder.setText(self.tr("Metadata folder: "))
        self.btn_browse_input_folder.setText(self.tr("Browse"))
        self.grp_udata.setTitle(self.tr("uData catalog"))
        self.lbl_udata_api_url_base.setText(self.tr("API URL:"))
        self.lbl_udata_api_version.setText(self.tr("API version:"))
        self.lbl_udata_api_key.setText(self.tr("API key:"))
        self.lbl_udata_organization_id.setText(self.tr("Organization ID (optional):"))
        self.grp_geonetwork.setTitle(self.tr("GeoNetwork catalog"))
        self.lbl_geonetwork_url_base.setText(self.tr("URL:"))
        self.lne_geonetwork_url_base.setPlaceholderText(
            "https://catalogue.example/geonetwork"
        )
        self.lbl_geonetwork_portal.setText(self.tr("Portal:"))
        self.lbl_geonetwork_username.setText(self.tr("Username:"))
        self.lbl_geonetwork_password.setText(self.tr("Password:"))
        self.lbl_geonetwork_authcfg.setText(self.tr("QGIS authentication ID:"))
        self.lbl_geonetwork_group.setText(self.tr("Group ID:"))
        self.lbl_geonetwork_categories.setText(
            self.tr("Category IDs (comma separated, optional):")
        )
        self.lbl_geonetwork_update_mode.setText(
            self.tr("Records already in the catalog:")
        )
        self.cbb_geonetwork_update_mode.setItemText(
            self.cbb_geonetwork_update_mode.findData(
                GeonetworkUpdateModes.overwrite.value
            ),
            self.tr("Overwrite them"),
        )
        self.cbb_geonetwork_update_mode.setItemText(
            self.cbb_geonetwork_update_mode.findData(
                GeonetworkUpdateModes.complete.value
            ),
            self.tr("Only fill their empty fields"),
        )
        self.cbx_geonetwork_publish_to_all.setText(
            self.tr("Make the records visible to everyone")
        )
        self.cbx_geonetwork_reject_if_invalid.setText(
            self.tr("Reject the records invalid against the schema")
        )
        self.grp_report.setTitle(self.tr("Publication report"))
        self.wdg_publish_errors.tbw_content.setHorizontalHeaderLabels(
            [
                self.tr("File"),
                self.tr("Detail"),
            ]
        )


# #############################################################################
# ##### Stand alone program ########
# ##################################

if __name__ == "__main__":
    """To test"""
    import sys

    from dicogis.ui.qt_compat.QtWidgets import QApplication

    app = QApplication(sys.argv)
    widget = TabPublish()
    widget.show()
    sys.exit(app.exec())
