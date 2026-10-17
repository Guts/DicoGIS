#! python3  # noqa: E265


"""
Name:         TabFiles
Purpose:      Tab containing files widgets in DicoGIS Notebook.

Author:       Julien Moura (@geojulien)
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import logging
from pathlib import Path

# project
from dicogis.constants import FormatsRaster
from dicogis.ui.qt_compat import uic
from dicogis.ui.qt_compat.QtCore import pyqtSignal
from dicogis.ui.qt_compat.QtWidgets import QFileDialog, QMessageBox, QWidget
from dicogis.utils.check_path import check_path
from dicogis.utils.environment import (
    get_available_gdal_drivers,
    is_format_supported_by_gdal,
)
from dicogis.utils.utils import Utilities


# ##############################################################################
# ############ Globals ############
# #################################

logger = logging.getLogger(__name__)

# format filter checkboxes (.ui objectName) mapped to the FormatsVector member
# name gating their driver availability (dicogis.constants.FORMAT_TO_GDAL_DRIVERS)
CHECKBOX_TO_FORMAT: dict[str, str] = {
    "cbx_shp": "esri_shapefile",
    "cbx_tab": "mapinfo_tab",
    "cbx_kml": "kml",
    "cbx_gml": "gml",
    "cbx_geoj": "geojson",
    "cbx_gxt": "gxt",
    "cbx_dxf": "dgn",
    "cbx_egdb": "file_geodatabase_esri",
    "cbx_gpkg": "file_geodatabase_geopackage",
    "cbx_spadb": "file_geodatabase_spatialite",
}
# cbx_rast covers 3 formats at once (no per-format checkbox): available as
# soon as GDAL can read at least one of them (GeoTIFF is a core driver, so
# this is only ever False on a very unusual GDAL build).
RASTER_FORMATS: tuple[str, ...] = ("ecw", "geotiff", "jpeg")

# ##############################################################################
# ########## Classes ###############
# ##################################


class TabFiles(QWidget):
    """Tab for listing and picking geodata files formats.

    Args:
        QWidget: inherited Qt widget
    """

    folder_selected = pyqtSignal(str)

    def __init__(
        self,
        parent: QWidget | None = None,
        listing_initial_folder: Path | None = None,
    ):
        """Initializes UI tab for files browsing and filtering.

        Args:
            parent: Qt parent widget
            listing_initial_folder: initial folder for the browse dialog. Defaults
                to Path().home().
        """
        super().__init__(parent)
        uic.loadUi(
            Utilities().resolve_internal_path(
                internal_path=Path("ui/wdg_tab_files.ui")
            ),
            self,
        )

        # browse default path
        self.listing_initial_folder_path = listing_initial_folder
        if not self.listing_initial_folder_path:
            self.listing_initial_folder_path = Path().home()

        self.cbx_rast.setText(
            "rasters ({})".format(
                ", ".join([raster_format.value for raster_format in FormatsRaster])
            )
        )

        self.btn_browse.clicked.connect(self.on_browse_get_initial_listing_folder_path)

        self.retranslate_ui()
        self.disable_unsupported_format_filters()

    def disable_unsupported_format_filters(self) -> None:
        """Grey out (and uncheck) filters for formats the installed GDAL
        build cannot actually read. Some drivers (e.g. Geoconcept, ECW) are
        optional/plugin drivers not included in every GDAL packaging."""
        available_drivers = get_available_gdal_drivers()
        unavailable_tooltip = self.tr(
            "Not available: the installed GDAL build does not include the "
            "driver required for this format."
        )

        for checkbox_name, format_name in CHECKBOX_TO_FORMAT.items():
            if is_format_supported_by_gdal(format_name, available_drivers):
                continue
            checkbox = getattr(self, checkbox_name)
            checkbox.setChecked(False)
            checkbox.setEnabled(False)
            checkbox.setToolTip(unavailable_tooltip)

        if not any(
            is_format_supported_by_gdal(format_name, available_drivers)
            for format_name in RASTER_FORMATS
        ):
            self.cbx_rast.setChecked(False)
            self.cbx_rast.setEnabled(False)
            self.cbx_rast.setToolTip(unavailable_tooltip)

    def on_browse_get_initial_listing_folder_path(self) -> Path | None:
        """Browse and insert the path of target folder.

        Returns:
            selected folder path or None if something went wrong
        """
        try:
            check_path(
                input_path=self.listing_initial_folder_path,
                must_be_a_folder=True,
                must_be_a_file=False,
                must_exists=True,
            )
        except Exception as err:
            logger.error(
                f"Initial listing folder ({self.listing_initial_folder_path}) is not a "
                f"valid existing folder. Fallback to user's home. Trace: {err}"
            )
            self.listing_initial_folder_path = Path().home()

        foldername = QFileDialog.getExistingDirectory(
            self,
            self.tr("Any folder selected"),
            str(self.listing_initial_folder_path),
        )

        # check if a folder has been choosen
        if not foldername:
            QMessageBox.information(
                self,
                self.tr("Any folder selected"),
                self.tr("Any folder selected"),
            )
            return None

        self.lne_target.setText(foldername)

        # let the owning window react (default output filename, launch scan worker)
        self.folder_selected.emit(foldername)

        # end of function
        return Path(foldername)

    # -- Accessors used by OptionsManager -------------------------------------------

    def get_target_path(self) -> str:
        """Return the currently entered target folder path."""
        return self.lne_target.text()

    def set_target_path(self, path: str) -> None:
        """Set the target folder path."""
        self.lne_target.setText(path)

    def get_filters_state(self) -> dict[str, bool]:
        """Return the state of every format filter checkbox."""
        return {
            "opt_shp": self.cbx_shp.isChecked(),
            "opt_tab": self.cbx_tab.isChecked(),
            "opt_kml": self.cbx_kml.isChecked(),
            "opt_gml": self.cbx_gml.isChecked(),
            "opt_geoj": self.cbx_geoj.isChecked(),
            "opt_gxt": self.cbx_gxt.isChecked(),
            "opt_rast": self.cbx_rast.isChecked(),
            "opt_egdb": self.cbx_egdb.isChecked(),
            "opt_gpkg": self.cbx_gpkg.isChecked(),
            "opt_spadb": self.cbx_spadb.isChecked(),
            "opt_dxf": self.cbx_dxf.isChecked(),
        }

    def set_filters_state(self, values: dict) -> None:
        """Apply the state of every format filter checkbox from a dict."""
        mapping = {
            "opt_shp": self.cbx_shp,
            "opt_tab": self.cbx_tab,
            "opt_kml": self.cbx_kml,
            "opt_gml": self.cbx_gml,
            "opt_geoj": self.cbx_geoj,
            "opt_gxt": self.cbx_gxt,
            "opt_rast": self.cbx_rast,
            "opt_egdb": self.cbx_egdb,
            "opt_gpkg": self.cbx_gpkg,
            "opt_spadb": self.cbx_spadb,
            "opt_dxf": self.cbx_dxf,
        }
        for key, checkbox in mapping.items():
            if key in values:
                checkbox.setChecked(bool(int(values[key])))

    def retranslate_ui(self) -> None:
        """Update widgets texts for the currently active language."""
        self.grp_path.setTitle(self.tr(" Folders structure target "))
        self.grp_filters.setTitle(self.tr(" Formats "))
        self.lbl_target.setText(self.tr("Folder path: "))
        self.btn_browse.setText(self.tr("Browse"))


# #############################################################################
# ##### Stand alone program ########
# ##################################

if __name__ == "__main__":
    """To test"""
    import sys

    from dicogis.ui.qt_compat.QtWidgets import QApplication

    app = QApplication(sys.argv)
    widget = TabFiles()
    widget.show()
    sys.exit(app.exec())
