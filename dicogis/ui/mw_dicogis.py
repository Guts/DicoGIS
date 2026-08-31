#! python3  # noqa: E265


"""
DicoGIS
Automatize the creation of a dictionnary of geographic data
            contained in a folders structures.
            It produces an Excel output file (.xlsx)

Julien Moura (@geojulien)
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# standard library
import getpass
import locale
import logging
from datetime import date
from pathlib import Path
from sys import platform as opersys

# 3rd party
from osgeo import gdal

# GUI
from PyQt6 import uic
from PyQt6.QtCore import QThread, QTranslator
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QWidget
from typer import launch

# Project
from dicogis import __about__
from dicogis.cli.cmd_inventory import determine_output_path
from dicogis.cli.cmd_publish import PublishReport
from dicogis.constants import AvailableLocales, OutputFormats
from dicogis.export.base_serializer import MetadatasetSerializerBase
from dicogis.export.to_xlsx import MetadatasetSerializerXlsx
from dicogis.georeaders.process_files import ProcessingFiles
from dicogis.georeaders.read_postgis import ReadPostGIS
from dicogis.ui.wdg_misc_buttons import MiscButtons
from dicogis.ui.wdg_tab_credits import TabCredits
from dicogis.ui.wdg_tab_database import TabDatabaseServer
from dicogis.ui.wdg_tab_files import TabFiles
from dicogis.ui.wdg_tab_publish import TabPublish
from dicogis.ui.wdg_tab_settings import TabSettings
from dicogis.ui.workers import (
    FolderScanWorker,
    PostgisProcessingWorker,
    ProcessingWorker,
    PublishWorker,
    QtProgressReporter,
)
from dicogis.utils.checknorris import CheckNorris
from dicogis.utils.notifier import send_system_notify
from dicogis.utils.options import OptionsManager
from dicogis.utils.texts import TextsManager
from dicogis.utils.utils import Utilities

# ##############################################################################
# ############ Globals ############
# #################################


utils_global = Utilities()

# LOG
logger = logging.getLogger(__name__)


# ##############################################################################
# ############ Classes #############
# ##################################


class DicoGIS(QMainWindow):
    """Main DicoGIS GUI object.

    Args:
        QMainWindow: inherited Qt main window.
    """

    # attributes
    package_about = __about__

    def __init__(self, parent: QWidget | None = None):
        """Main window constructor."""
        super().__init__(parent)
        uic.loadUi(
            utils_global.resolve_internal_path(internal_path=Path("ui/mw_dicogis.ui")),
            self,
        )

        # store vars as attr
        self.txt_manager = TextsManager()
        self.dir_imgs = utils_global.resolve_internal_path(internal_path="bin/img")

        # manage settings outside the main class
        self.settings = OptionsManager()
        # Invoke Check Norris
        checker = CheckNorris()

        # basics settings
        self.setWindowTitle(f"DicoGIS {self.package_about.__version__}")
        self.uzer = getpass.getuser()
        self.setWindowIcon(QIcon(str(self.dir_imgs / "DicoGIS.ico")))

        # -- Variables --
        self.num_folders = 0
        self.def_lang = "EN"  # default language to start
        self.localized_strings = {}  # texts dictionary

        # formats / type: vectors
        self.li_vectors_formats = (
            ".shp",
            ".tab",
            ".kml",
            ".gml",
            ".geojson",
        )  # vectors handled
        self.li_shapefiles = []  # list for shapefiles path
        self.li_mapinfo_tab = []  # list for MapInfo tables path
        self.li_kml = []  # list for KML path
        self.li_gml = []  # list for GML path
        self.li_geojson = []  # list for GeoJSON paths
        self.li_geotiff = []  # list for GeoJSON paths
        self.li_gxt = []  # list for GXT paths
        self.li_vectors = []  # list for all vectors
        # formats / type: rasters
        self.li_raster = []  # list for rasters paths
        self.li_raster_formats = (".ecw", ".tif", ".jp2")  # raster handled
        # formats / type: file databases
        self.li_file_databases = []  # list for all files databases
        self.li_file_database_esri = []  # list for Esri File Geodatabases
        self.li_file_database_geopackage = []
        self.li_file_database_spatialite = []  # list for Spatialite Geodatabases
        # formats / type: CAO/DAO
        self.li_cdao = []  # list for all CAO/DAO files
        self.li_dxf = []  # list for AutoCAD DXF paths
        self.li_dwg = []  # list for AutoCAD DWG paths
        self.li_dgn = []  # list for MicroStation DGN paths

        # dictionaries to store informations
        self.dico_layer = {}  # dict for vectors informations
        self.dico_fields = {}  # dict for fields informations
        self.dico_raster = {}  # dict for rasters global informations
        self.dico_bands = {}  # dict for bands informations
        self.dico_fdb = {}  # dict for Esri FileGDB
        self.dico_cdao = {}  # dict for CAO/DAO
        self.dico_err = {}  # errors list

        # metrics
        self.dico_metrics = {}
        self.global_total_layers = 0
        self.global_total_fields = 0
        self.global_total_features = 0
        self.global_total_errors = 0
        self.global_total_warnings = 0
        self.global_total_srs_proj = 0
        self.global_total_srs_geog = 0
        self.global_total_srs_none = 0
        self.global_ignored = 0  # files ignored by an user filter
        self.global_dico_fields = {}

        # threads/workers references (kept to avoid premature garbage collection)
        self._scan_thread: QThread | None = None
        self._scan_worker: FolderScanWorker | None = None
        self._proc_thread: QThread | None = None
        self._proc_worker: object | None = None
        self._progress_reporter: QtProgressReporter | None = None

        # Qt translator for widget texts (self.tr()). Kept as an attribute so it can
        # be swapped out on language change without being garbage-collected.
        self._qt_translator: QTranslator | None = None

        # fillfulling text
        self.localized_strings = self.txt_manager.load_texts(
            language_code=self.def_lang
        )

        # tabs
        self.tab_files = TabFiles(parent=self.nb)  # tab_id = 0
        self.tab_sgbd = TabDatabaseServer(parent=self.nb)  # tab_id = 1
        self.tab_options = TabSettings(parent=self.nb)  # tab_id = 2
        self.tab_publish = TabPublish(parent=self.nb)  # tab_id = 3
        self.tab_credits = TabCredits(parent=self.nb)  # tab_id = 4

        self.nb.addTab(self.tab_files, " Files ")
        self.nb.addTab(self.tab_sgbd, " PostGIS ")
        self.nb.addTab(self.tab_options, "Options")
        self.nb.addTab(self.tab_publish, "Publish")
        self.nb.addTab(self.tab_credits, "Credits")

        self.tab_files.folder_selected.connect(self.on_folder_selected)

        # miscellaneous (left side panel)
        self.misc_frame = MiscButtons(self, images_folder=self.dir_imgs)
        self.main_layout.addWidget(self.misc_frame, 0, 0, 5, 1)

        # language switcher
        li_lang = [v.value for v in AvailableLocales]
        self.ddl_lang.addItems(li_lang)
        self.ddl_lang.setCurrentText(self.def_lang)
        self.ddl_lang.activated.connect(lambda _index: self.retranslate_ui())

        # Basic buttons
        self.val.setEnabled(True)
        self.val.clicked.connect(self.process)
        self.can.clicked.connect(self.close)
        self.btn_cancel.clicked.connect(self._on_cancel_clicked)

        # loading previous options
        if not self.settings.first_use:
            try:
                self.settings.load_settings(parent=self)
            except Exception as err:
                logger.error(
                    f"Load settings failed: option or section is missing. Trace: {err}"
                )

        self.retranslate_ui()

        # checking connection
        if not checker.check_internet_connection():
            self.nb.setTabEnabled(1, False)
            self.nb.setTabEnabled(2, False)
            self.nb.setTabEnabled(3, False)

    # =================================================================================

    def retranslate_ui(self) -> None:
        """Update widgets text with the language currently selected."""
        new_lang = self.ddl_lang.currentText()
        self._install_qt_translator(new_lang)
        # still needed for the shared processing pipeline (export/georeaders), which
        # has no PyQt6/Qt translator dependency of its own
        self.localized_strings = self.txt_manager.load_texts(language_code=new_lang)

        self.welcome.setText(self.tr("Hello ") + self.uzer)
        self.can.setText(self.tr("Quit"))
        self.FrOutp.setTitle(self.tr(" Output file "))
        self.FrProg.setTitle(self.tr("Progression"))
        self.val.setText(self.tr("Go!"))
        self.btn_cancel.setText(self.tr("Cancel"))
        self.lbl_outxl_filename.setText(self.tr("Name of output file: "))

        self.nb.setTabText(0, self.tr(" Files "))
        self.nb.setTabText(1, self.tr(" Database "))
        self.nb.setTabText(2, self.tr(" Settings "))
        self.nb.setTabText(3, self.tr("Publish"))
        self.nb.setTabText(4, self.tr(" Credits "))

        self.tab_files.retranslate_ui()
        self.tab_sgbd.retranslate_ui()
        self.tab_options.retranslate_ui()
        self.tab_publish.retranslate_ui()

        self._apply_locale(new_lang)

    def _install_qt_translator(self, language_code: str) -> None:
        """Install the Qt translator (.qm) matching the given language on the
        running QApplication, so every `self.tr()` call across the GUI resolves
        to that language.

        Args:
            language_code: 2 letters language code (EN, FR, ES)
        """
        app = QApplication.instance()
        if app is None:
            return

        if self._qt_translator is not None:
            app.removeTranslator(self._qt_translator)
            self._qt_translator = None

        # source strings are already English: no .qm is shipped/needed for EN,
        # removing any previously installed translator is enough
        if language_code.upper() == "EN":
            return

        translator = QTranslator(self)
        qm_path = utils_global.resolve_internal_path(
            internal_path=Path(f"ui/i18n/dicogis_{language_code.lower()}.qm")
        )
        if translator.load(str(qm_path)):
            app.installTranslator(translator)
            self._qt_translator = translator
        else:
            logger.warning(f"Qt translation file not found or invalid: {qm_path}")

    def _apply_locale(self, new_lang: str) -> None:
        """Set the OS locale according to the language passed.

        Args:
            new_lang: 2 letters language code (EN, FR, ES)
        """
        try:
            if opersys == "win32":
                if new_lang.lower() == "fr":
                    locale.setlocale(locale.LC_ALL, "fra_fra")
                elif new_lang.lower() == "es":
                    locale.setlocale(locale.LC_ALL, "esp_esp")
                else:
                    locale.setlocale(locale.LC_ALL, "uk_UK")
            else:
                if new_lang.lower() == "fr":
                    locale.setlocale(locale.LC_ALL, "fr_FR.utf8")
                elif new_lang.lower() == "es":
                    locale.setlocale(locale.LC_ALL, "es_ES.utf8")
                else:
                    locale.setlocale(locale.LC_ALL, "en_GB.utf8")

            logger.info(f"Language switched to: {new_lang}")
        except locale.Error:
            logger.error("Selected locale is not installed")

    def set_status_message(self, message: str) -> None:
        """Update the status label text.

        Args:
            message: message to display.
        """
        self.lbl_status.setText(message)

    # =================================================================================
    # -- Folder listing (Files tab) ---------------------------------------------------

    def on_folder_selected(self, foldername: str) -> None:
        """React to a folder being picked in the Files tab: set the default output
        filename and start the background folder scan.

        Args:
            foldername: selected folder path.
        """
        self.ent_outxl_filename.setText(
            f"DicoGIS_{Path(foldername).name}_{date.today()}.xlsx"
        )
        self._start_folder_scan(foldername)

    def _start_folder_scan(self, target_folder: str) -> None:
        """Start a background worker listing geodata files under target_folder.

        Args:
            target_folder: folder to walk into.
        """
        self.tab_files.btn_browse.setEnabled(False)
        self.set_status_message(
            self.tr("Progress: parsing and retrieving compatible files")
        )
        # indeterminate: the number of folders can't be known before walking
        # the tree, so the scan reports a running count as a message instead
        self.prog_layers.setRange(0, 0)
        logger.info(f"Begin of folders parsing: {target_folder}")

        self._progress_reporter = QtProgressReporter(self)
        self._progress_reporter.message_changed.connect(self.set_status_message)
        self._enable_cancel_button(True)

        self._scan_thread = QThread(self)
        self._scan_worker = FolderScanWorker(
            target_folder,
            progress_reporter=self._progress_reporter,
            **self.tab_options.get_listing_scan_kwargs(),
        )
        self._scan_worker.moveToThread(self._scan_thread)
        self._scan_thread.started.connect(self._scan_worker.run)
        self._scan_worker.status_message.connect(self.set_status_message)
        self._scan_worker.finished.connect(self._on_folder_scan_finished)
        self._scan_worker.error.connect(self._on_folder_scan_error)
        self._scan_worker.canceled.connect(self._on_folder_scan_canceled)
        self._scan_worker.finished.connect(self._scan_thread.quit)
        self._scan_worker.error.connect(self._scan_thread.quit)
        self._scan_worker.canceled.connect(self._scan_thread.quit)
        self._scan_worker.finished.connect(self._scan_worker.deleteLater)
        self._scan_worker.error.connect(self._scan_worker.deleteLater)
        self._scan_worker.canceled.connect(self._scan_worker.deleteLater)
        self._scan_thread.finished.connect(self._scan_thread.deleteLater)
        self._scan_thread.finished.connect(self._clear_scan_thread_ref)
        self._scan_thread.start()

    def _clear_scan_thread_ref(self) -> None:
        """Drop the reference to the finished folder-scan thread."""
        self._scan_thread = None

    def _enable_cancel_button(self, enabled: bool) -> None:
        """Show/hide the cancel button along a cancellable operation.

        Args:
            enabled: whether a cancellable operation is running.
        """
        self.btn_cancel.setVisible(enabled)
        self.btn_cancel.setEnabled(enabled)

    def _on_cancel_clicked(self) -> None:
        """Ask the running operation to stop at its next cancellation check."""
        if self._progress_reporter is None:
            return
        logger.info("Cancellation requested by the user.")
        self.btn_cancel.setEnabled(False)
        self.set_status_message(self.tr("Canceling..."))
        self._progress_reporter.request_cancel()

    def _reset_progress_after_interruption(self) -> None:
        """Put the progress widgets back to their idle state."""
        self._enable_cancel_button(False)
        self.prog_layers.setRange(0, 1)
        self.prog_layers.setValue(0)
        self.tab_files.btn_browse.setEnabled(True)

    def _on_folder_scan_canceled(self) -> None:
        """React to a folder scan interrupted by the user."""
        logger.info("Folder scan canceled by the user.")
        self._reset_progress_after_interruption()
        self.set_status_message(self.tr("Folder scan canceled."))

    def _on_folder_scan_error(self, message: str) -> None:
        """React to a folder scan failure.

        Args:
            message: error message.
        """
        logger.error(f"Folder scan failed: {message}")
        self._reset_progress_after_interruption()
        QMessageBox.critical(self, "DicoGIS", message)

    def _on_folder_scan_finished(self, result: tuple) -> None:
        """React to a successful folder scan: store the resulting file lists.

        Args:
            result: tuple returned by find_geodata_files().
        """
        (
            self.num_folders,
            self.li_shapefiles,
            self.li_mapinfo_tab,
            self.li_kml,
            self.li_gml,
            self.li_geojson,
            self.li_geotiff,
            self.li_gxt,
            self.li_raster,
            self.li_file_database_esri,
            self.li_dxf,
            self.li_dwg,
            self.li_dgn,
            self.li_cdao,
            self.li_file_databases,
            self.li_file_database_spatialite,
            self.li_file_database_geopackage,
        ) = result

        # end of listing
        self._enable_cancel_button(False)
        self.prog_layers.setRange(0, 1)
        self.prog_layers.setValue(0)

        # status message
        self.set_status_message(
            "{} shapefiles - "
            "{} tables (MapInfo) - "
            "{} KML - "
            "{} GML - "
            "{} GeoJSON - "
            "{} GXT"
            "\n{} rasters - "
            "{} file databases - "
            "{} CAO/DAO - "
            "in {}{}".format(
                len(self.li_shapefiles),
                len(self.li_mapinfo_tab),
                len(self.li_kml),
                len(self.li_gml),
                len(self.li_geojson),
                len(self.li_gxt),
                len(self.li_raster),
                len(self.li_file_databases),
                len(self.li_cdao),
                self.num_folders,
                self.tr(" folders."),
            )
        )

        # grouping vectors lists
        self.li_vectors = []
        self.li_vectors.extend(self.li_shapefiles)
        self.li_vectors.extend(self.li_mapinfo_tab)
        self.li_vectors.extend(self.li_kml)
        self.li_vectors.extend(self.li_gml)
        self.li_vectors.extend(self.li_geojson)
        self.li_vectors.extend(self.li_gxt)

        # reactivating the buttons
        self.tab_files.btn_browse.setEnabled(True)
        self.val.setEnabled(True)

    # =================================================================================
    # -- Processing dispatch ------------------------------------------------------------

    def process(self) -> None:
        """Check needed info and launch different processes."""
        self.typo: int = self.nb.currentIndex()
        logger.info(f"Selected tab: {self.typo}")

        if self.typo not in (0, 1, 3):
            logger.debug("Active tab does not allow execution.")
            return

        # saving settings
        self.settings.save_settings(self)

        # disabling UI to avoid unattended actions
        self.val.setEnabled(False)
        self.nb.setTabEnabled(0, False)
        self.nb.setTabEnabled(1, False)
        self.nb.setTabEnabled(2, False)
        self.nb.setTabEnabled(3, False)

        # check form fields
        if not self.check_fields(tab_data_type=self.typo):
            self._on_check_failed()
            return

        # uData publication has its own dedicated pipeline: no output serializer,
        # no geodata listing, no PostGIS connection needed.
        if self.typo == 3:
            logger.info("PROCESS LAUNCHED: uData publication")
            self.process_publish()
            return

        # if SGBD, check connection
        pg_reader = None
        if self.typo == 1:
            pg_reader = self.test_connection()
            if pg_reader is None:
                self._on_check_failed()
                return

        # creating the output serializer
        self.serializer: MetadatasetSerializerXlsx = (
            MetadatasetSerializerBase.get_serializer_from_parameters(
                format_or_serializer=OutputFormats.excel,
                localized_strings=self.localized_strings,
                output_path=None,
                opt_prettify_size=self.tab_options.opt_export_size_prettify.isChecked(),
                opt_raw_path=self.tab_options.opt_export_raw_path.isChecked(),
            )
        )

        self.lbl_status.setStyleSheet("color: DodgerBlue;")
        self.set_status_message("Excel worbook object instanciated")

        # process files or PostGIS database
        if self.typo == 0:
            self.nb.setCurrentIndex(0)
            logger.info("PROCESS LAUNCHED: files")
            self.process_files()
        elif self.typo == 1:
            self.nb.setCurrentIndex(1)
            self.serializer.pre_serializing(has_sgbd=1)
            logger.info("PROCESS LAUNCHED: SGBD")
            self.process_db(sgbd_reader=pg_reader)
        else:
            logger.critical("Unrecognized data type to process. Report it!")

    def _enable_processing_controls(self) -> None:
        """Re-enable the controls disabled while a process was running."""
        self.val.setEnabled(True)
        self.nb.setTabEnabled(0, True)
        self.nb.setTabEnabled(1, True)
        self.nb.setTabEnabled(2, True)
        self.nb.setTabEnabled(3, True)

    def _on_check_failed(self) -> None:
        """React to a check_fields()/test_connection() failure."""
        self.lbl_status.setStyleSheet("color: red;")
        self._enable_processing_controls()
        self.nb.setCurrentIndex(self.typo)

    def _on_processing_error(self, message: str) -> None:
        """React to a processing worker failure.

        Args:
            message: error message.
        """
        logger.error(f"Processing failed: {message}")
        self.lbl_status.setStyleSheet("color: red;")
        self._enable_cancel_button(False)
        self._enable_processing_controls()
        QMessageBox.critical(self, "DicoGIS", message)

    def process_files(self) -> None:
        """Launch files processing in a background worker."""
        # check if there are some layers into the folder structure
        if not (
            len(self.li_vectors)
            + len(self.li_raster)
            + len(self.li_file_databases)
            + len(self.li_cdao)
        ):
            QMessageBox.critical(
                self,
                "DicoGIS - User error",
                self.tr("Any compatible geographic data (.shp / .tab) has been found."),
            )
            self._enable_processing_controls()
            return

        # set output path
        if self.serializer.output_path is None:
            self.serializer.output_path = Path(
                self.tab_files.get_target_path()
            ).joinpath(self.ent_outxl_filename.text())

        logger.info(f"Output path: {self.serializer.output_path.resolve()}")

        self._progress_reporter = QtProgressReporter(self)
        self._progress_reporter.message_changed.connect(self.set_status_message)
        self._progress_reporter.progress_incremented.connect(self.prog_layers.setValue)
        self._progress_reporter.total_changed.connect(self.prog_layers.setMaximum)

        # instanciate geofiles processor
        geofiles_processor = ProcessingFiles(
            serializer=self.serializer,
            localized_strings=self.localized_strings,
            # list by tabs
            li_vectors=self.li_vectors,
            li_rasters=self.li_raster,
            li_file_databases=self.li_file_databases,
            li_cdao=self.li_cdao,
            # list by formats
            li_dxf=self.li_dxf,
            li_flat_geodatabase_esri_filegdb=self.li_file_database_esri,
            li_flat_geodatabase_spatialite=self.li_file_database_spatialite,
            li_flat_geodatabase_geopackage=self.li_file_database_geopackage,
            li_gml=self.li_gml,
            li_gxt=self.li_gxt,
            li_kml=self.li_kml,
            li_shapefiles=self.li_shapefiles,
            li_mapinfo_tab=self.li_mapinfo_tab,
            li_geojson=self.li_geojson,
            li_geotiff=self.li_geotiff,
            # options
            opt_analyze_cdao=self.tab_files.opt_dxf.isChecked(),
            opt_analyze_esri_filegdb=self.tab_files.opt_egdb.isChecked(),
            opt_analyze_geopackage=self.tab_files.opt_gpkg.isChecked(),
            opt_analyze_geojson=self.tab_files.opt_geoj.isChecked(),
            opt_analyze_gml=self.tab_files.opt_gml.isChecked(),
            opt_analyze_gxt=self.tab_files.opt_gxt.isChecked(),
            opt_analyze_kml=self.tab_files.opt_kml.isChecked(),
            opt_analyze_mapinfo_tab=self.tab_files.opt_tab.isChecked(),
            opt_analyze_raster=self.tab_files.opt_rast.isChecked(),
            opt_analyze_shapefiles=self.tab_files.opt_shp.isChecked(),
            opt_analyze_spatialite=self.tab_files.opt_spadb.isChecked(),
            # progress
            progress_reporter=self._progress_reporter,
            # misc
            opt_quick_fail=self.tab_options.opt_quick_fail.isChecked(),
        )

        # sheets and progress bar
        total_files = geofiles_processor.count_files_to_process()
        self.prog_layers.setMaximum(total_files)

        # launch processing in a background thread
        self._enable_cancel_button(True)
        self._proc_thread = QThread(self)
        self._proc_worker = ProcessingWorker(geofiles_processor)
        self._proc_worker.moveToThread(self._proc_thread)
        self._proc_thread.started.connect(self._proc_worker.run)
        self._proc_worker.finished.connect(self._on_files_processing_finished)
        self._proc_worker.error.connect(self._on_processing_error)
        self._proc_worker.canceled.connect(self._on_processing_canceled)
        self._proc_worker.finished.connect(self._proc_thread.quit)
        self._proc_worker.error.connect(self._proc_thread.quit)
        self._proc_worker.canceled.connect(self._proc_thread.quit)
        self._proc_worker.finished.connect(self._proc_worker.deleteLater)
        self._proc_worker.error.connect(self._proc_worker.deleteLater)
        self._proc_worker.canceled.connect(self._proc_worker.deleteLater)
        self._proc_thread.finished.connect(self._proc_thread.deleteLater)
        self._proc_thread.finished.connect(self._clear_proc_thread_ref)
        self._proc_thread.start()

    def _on_files_processing_finished(self, total_files: int) -> None:
        """React to a successful files processing run.

        Args:
            total_files: number of files processed.
        """
        self._enable_cancel_button(False)
        launch(url=f"{self.serializer.output_path.resolve()}")
        send_system_notify(
            notification_title="DicoGIS analysis ended",
            notification_message=f"DicoGIS successfully processed {total_files} files. "
            "\nOpen the application to save the workbook.",
            notification_sound=self.tab_options.opt_end_process_notification_sound.isChecked(),
        )
        self._enable_processing_controls()

    def _on_processing_canceled(self) -> None:
        """React to a processing run interrupted by the user.

        Whatever was processed before the cancellation has still been written
        to the output file, so it's offered rather than silently discarded.
        """
        logger.info("Processing canceled by the user.")
        self._enable_cancel_button(False)
        self.prog_layers.setValue(0)
        self._enable_processing_controls()
        self.set_status_message(
            self.tr("Processing canceled. Partial results were saved to the output.")
        )

    def process_db(self, sgbd_reader: ReadPostGIS) -> None:
        """Launch PostGIS DB analysis in a background worker.

        Args:
            sgbd_reader: PostGIS georeader
        """
        logger.info("Start processing PostGIS tables...")

        pg_service_name = self.tab_sgbd.get_selected_pg_service()

        # set the default output file in UI and as serializer attribute
        self.ent_outxl_filename.setText(
            str(
                determine_output_path(
                    output_path=None,
                    output_format="excel",
                    pg_services=[pg_service_name],
                )
            )
        )
        self.serializer.output_path = Path(self.ent_outxl_filename.text())

        self._progress_reporter = QtProgressReporter(self)
        self._progress_reporter.message_changed.connect(self.set_status_message)
        self._progress_reporter.progress_incremented.connect(self.prog_layers.setValue)
        self._progress_reporter.total_changed.connect(self.prog_layers.setMaximum)

        self._proc_thread = QThread(self)
        self._proc_worker = PostgisProcessingWorker(
            sgbd_reader=sgbd_reader,
            serializer=self.serializer,
            progress_reporter=self._progress_reporter,
        )
        self._enable_cancel_button(True)
        self._proc_worker.moveToThread(self._proc_thread)
        self._proc_thread.started.connect(self._proc_worker.run)
        self._proc_worker.finished.connect(self._on_db_processing_finished)
        self._proc_worker.error.connect(self._on_processing_error)
        self._proc_worker.canceled.connect(self._on_processing_canceled)
        self._proc_worker.finished.connect(self._proc_thread.quit)
        self._proc_worker.error.connect(self._proc_thread.quit)
        self._proc_worker.canceled.connect(self._proc_thread.quit)
        self._proc_worker.finished.connect(self._proc_worker.deleteLater)
        self._proc_worker.error.connect(self._proc_worker.deleteLater)
        self._proc_worker.canceled.connect(self._proc_worker.deleteLater)
        self._proc_thread.finished.connect(self._proc_thread.deleteLater)
        self._proc_thread.finished.connect(self._clear_proc_thread_ref)
        self._proc_thread.start()

    def _clear_proc_thread_ref(self) -> None:
        """Drop the reference to the finished processing thread."""
        self._proc_thread = None

    def _on_db_processing_finished(self, total_layers: int) -> None:
        """React to a successful PostGIS processing run.

        Args:
            total_layers: number of PostGIS tables processed.
        """
        launch(url=f"{self.serializer.output_path.resolve()}")
        send_system_notify(
            notification_title="DicoGIS analysis ended",
            notification_message="DicoGIS successfully processed "
            f"{total_layers} PostGIS tables. "
            "\nOpen the application to save the workbook.",
            notification_sound=self.tab_options.opt_end_process_notification_sound.isChecked(),
        )
        self._enable_processing_controls()

    def process_publish(self) -> None:
        """Launch uData publication of metadata JSON files in a background worker."""
        self._progress_reporter = None
        self.prog_layers.setRange(0, 0)  # indeterminate mode while fetching the catalog
        self.set_status_message("Publishing to uData...")
        self.tab_publish.clear_report()

        self._proc_thread = QThread(self)
        self._proc_worker = PublishWorker(
            input_folder=Path(self.tab_publish.get_input_folder()),
            udata_api_key=self.tab_publish.get_udata_api_key(),
            udata_api_url_base=self.tab_publish.get_udata_api_url_base(),
            udata_api_version=self.tab_publish.get_udata_api_version(),
            udata_organization_id=self.tab_publish.get_udata_organization_id(),
        )
        self._proc_worker.moveToThread(self._proc_thread)
        self._proc_thread.started.connect(self._proc_worker.run)
        self._proc_worker.progress_changed.connect(self._on_publish_progress)
        self._proc_worker.finished.connect(self._on_publish_finished)
        self._proc_worker.error.connect(self._on_processing_error)
        self._proc_worker.finished.connect(self._proc_thread.quit)
        self._proc_worker.error.connect(self._proc_thread.quit)
        self._proc_worker.finished.connect(self._proc_worker.deleteLater)
        self._proc_worker.error.connect(self._proc_worker.deleteLater)
        self._proc_thread.finished.connect(self._proc_thread.deleteLater)
        self._proc_thread.finished.connect(self._clear_proc_thread_ref)
        self._proc_thread.start()

    def _on_publish_progress(self, files_done: int, files_total: int) -> None:
        """React to a uData publication progress update.

        Args:
            files_done: number of JSON files already examined.
            files_total: total number of JSON files to examine.
        """
        if self.prog_layers.maximum() != files_total:
            self.prog_layers.setRange(0, files_total)
        self.prog_layers.setValue(files_done)
        self.set_status_message(f"Publishing to uData: {files_done}/{files_total}")

    def _on_publish_finished(self, report: PublishReport) -> None:
        """React to a successful uData publication run.

        Args:
            report: outcome of the publication run.
        """
        self.prog_layers.setRange(0, max(report.total, 1))
        self.prog_layers.setValue(report.total)
        self.set_status_message(
            f"{report.published} published, {report.ignored} ignored, "
            f"{report.failed} failed."
        )
        self.tab_publish.show_report(report)
        send_system_notify(
            notification_title="DicoGIS publication ended",
            notification_message=f"{report.published} published, "
            f"{report.ignored} ignored,"
            f"{report.failed} failed.",
            notification_sound=self.tab_options.opt_end_process_notification_sound.isChecked(),
        )
        self._enable_processing_controls()

    def check_fields(self, tab_data_type: int) -> bool:
        """Check if required form fields are not empty.

        Args:
            tab_data_type: form's tab to check

        Returns:
            True if everything is OK
        """
        if tab_data_type == 0:
            if not len(self.tab_files.get_target_path()):
                QMessageBox.critical(
                    self, "DicoGIS - User error", self.tr("Any folder selected")
                )
                return False

            # check if at least a format has been choosen
            filters = self.tab_files.get_filters_state()
            if not (
                filters["opt_shp"]
                or filters["opt_tab"]
                or filters["opt_kml"]
                or filters["opt_gml"]
                or filters["opt_geoj"]
                or filters["opt_rast"]
                or filters["opt_egdb"]
                or filters["opt_gpkg"]
                or filters["opt_spadb"]
                or filters["opt_dxf"]
            ):
                QMessageBox.critical(
                    self, "DicoGIS - User error", self.tr("Any format selected")
                )
                return False

        elif tab_data_type == 1:
            if not self.tab_sgbd.get_selected_pg_service():
                self.tab_sgbd.ddl_pg_services.setStyleSheet("color: red;")
                self.set_status_message(
                    f"PG service name is a {self.tr('required field')}"
                )
                return False

        elif tab_data_type == 3:
            if not self.tab_publish.get_input_folder():
                QMessageBox.critical(
                    self, "DicoGIS - User error", self.tr("Any folder selected")
                )
                return False
            if not self.tab_publish.get_udata_api_key():
                QMessageBox.critical(
                    self,
                    "DicoGIS - User error",
                    self.tr("A uData API key is required to publish."),
                )
                return False

        # no error detected: let's test connection
        logger.info("Required fields are OK.")

        return True

    def test_connection(self) -> ReadPostGIS | None:
        """Test database connection.

        Returns:
            Optional[ReadPostGIS]: PostGIS reader or None
        """
        # check if a proxy is needed
        # more information about the GDAL HTTP proxy options here:
        # http://trac.osgeo.org/gdal/wiki/ConfigOptions#GDALOGRHTTPoptions
        if self.tab_options.FrOptProxy.isChecked():
            logger.info("Proxy configured.")
            gdal.SetConfigOption(
                "GDAL_HTTP_PROXY",
                f"{self.tab_options.prox_ent_host.text()}:"
                f"{self.tab_options.prox_ent_port.value()}",
            )
            if self.tab_options.opt_ntlm.isChecked():
                # NTLM: GDAL negotiates credentials itself, so this is an
                # intentionally empty "user:password" placeholder, not a
                # real secret.
                gdal.SetConfigOption("GDAL_PROXY_AUTH", "NTLM")
                gdal.SetConfigOption("GDAL_HTTP_PROXYUSERPWD", " : ")  # NOSONAR
        else:
            logger.info("No proxy configured.")

        # testing connection settings
        sgbd_reader = ReadPostGIS(
            service=self.tab_sgbd.get_selected_pg_service(),
            views_included=self.tab_sgbd.get_views_enabled(),
        )
        sgbd_reader.get_connection()

        # check connection state
        if sgbd_reader.conn is None:
            fail_reason = sgbd_reader.db_connection.state_msg
            self.set_status_message(f"Connection failed: {fail_reason}.")
            logger.error(f"PostGIS connection failed: {fail_reason}.")
            QMessageBox.critical(
                self,
                self.tr("Connection failed"),
                fail_reason,
            )
            return None

        self.set_status_message(
            f"{sgbd_reader.conn.GetLayerCount()} tables found in PostGIS database."
        )

        return sgbd_reader

    # =================================================================================
    # -- Accessors used by OptionsManager -----------------------------------------------

    def get_selected_language(self) -> str:
        """Return the currently selected language code."""
        return self.ddl_lang.currentText()

    def set_selected_language(self, language_code: str) -> None:
        """Select a language and retranslate the UI.

        Args:
            language_code: 2 letters language code (EN, FR, ES)
        """
        if AvailableLocales.has_value(language_code):
            self.ddl_lang.setCurrentText(language_code)

    def get_active_tab_index(self) -> int:
        """Return the currently active tab index."""
        return self.nb.currentIndex()

    def set_active_tab_index(self, index: int) -> None:
        """Select the active tab by index.

        Args:
            index: tab index to select.
        """
        self.nb.setCurrentIndex(int(index))

    # =================================================================================

    def closeEvent(self, event) -> None:
        """Ensure background threads are stopped before the window closes."""
        for thread in (self._scan_thread, self._proc_thread):
            if thread is not None and thread.isRunning():
                thread.quit()
                thread.wait(3000)
        super().closeEvent(event)
