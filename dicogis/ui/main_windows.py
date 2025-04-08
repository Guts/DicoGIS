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
import platform
from pathlib import Path
from sys import platform as opersys

# GUI
from tkinter import ACTIVE, DISABLED, END, NORMAL, Image, IntVar, StringVar
from tkinter.messagebox import showerror as avert
from tkinter.ttk import (
    Button,
    Combobox,
    Entry,
    Label,
    Labelframe,
    Notebook,
    Progressbar,
)
from typing import Optional

# 3rd party
from osgeo import gdal
from ttkthemes import ThemedTk
from typer import launch

# Project
from dicogis import __about__
from dicogis.cli.cmd_inventory import determine_output_path
from dicogis.constants import AvailableLocales, OutputFormats
from dicogis.export.base_serializer import MetadatasetSerializerBase
from dicogis.export.to_xlsx import MetadatasetSerializerXlsx
from dicogis.georeaders.process_files import ProcessingFiles
from dicogis.georeaders.read_postgis import ReadPostGIS
from dicogis.listing.geodata_listing import find_geodata_files
from dicogis.ui import MiscButtons, TabCredits, TabDatabaseServer, TabFiles, TabSettings
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


class DicoGIS(ThemedTk):
    """Main DicoGIS GUI object.

    Args:
        ThemedTk: themed tk object.
    """

    # attributes
    package_about = __about__

    def __init__(self, theme: str = "radiance"):
        """Main window constructor.

        Args:
            theme: Tkinter theme to use. Defaults to "radiance".
        """
        # store vars as attr
        self.txt_manager = TextsManager()
        self.dir_imgs = utils_global.resolve_internal_path(internal_path="bin/img")

        # manage settings outside the main class
        self.settings = OptionsManager("options.ini")
        # Invoke Check Norris
        checker = CheckNorris()

        # basics settings
        ThemedTk.__init__(self, fonts=True, themebg=True)
        self.set_theme(theme)
        self.title(f"DicoGIS {self.package_about.__version__}")
        self.uzer = getpass.getuser()
        if opersys == "win32":
            self.iconbitmap(self.dir_imgs / "DicoGIS.ico")  # windows icon
        elif opersys.startswith("linux"):
            icon = Image("photo", file=self.dir_imgs / "DicoGIS_logo.gif")
            self.call("wm", "iconphoto", self._w, icon)
        else:
            logger.warning(f"Unknown operating system: {platform.platform()}")
        self.resizable(width=False, height=False)
        self.focus_force()

        # -- Variables --
        # settings
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

        # fillfulling text
        self.localized_strings = self.txt_manager.load_texts(
            language_code=self.def_lang
        )

        # Notebook
        self.nb = Notebook(self)
        # tabs
        self.tab_files = TabFiles(
            parent=self.nb, localized_strings=self.localized_strings
        )  # tab_id = 0
        self.tab_sgbd = TabDatabaseServer(
            parent=self.nb, localized_strings=self.localized_strings, init_widgets=True
        )  # tab_id = 1
        self.tab_options = TabSettings(
            parent=self.nb,
            localized_strings=self.localized_strings,
            init_widgets=True,
            switcher=utils_global.ui_switch,
        )  # tab_id = 2
        self.tab_credits = TabCredits(parent=self.nb)  # tab_id = 3

        # =================================================================================
        # ## TAB 1: FILES ##
        self.nb.add(self.tab_files, text=" Files ", padding=3)

        # ================================================================================

        # ## TAB 2: Database ##
        self.nb.add(self.tab_sgbd, text=" PostGIS ", padding=3)

        # =================================================================================

        # ## TAB 3: Options ##
        self.nb.add(self.tab_options, text="Options", padding=3)

        # =================================================================================

        # ## TAB 4: Options ##
        self.nb.add(self.tab_credits, text="Credits", padding=3)

        # =================================================================================
        # ## MAIN FRAME ##
        # welcome message
        self.welcome = Label(
            self, text=self.localized_strings.get("hi") + self.uzer, foreground="blue"
        )

        # Frame: Output
        self.FrOutp = Labelframe(
            self, name="output", text=self.localized_strings.get("gui_fr4")
        )
        # widgets
        self.lbl_outxl_filename = Label(
            self.FrOutp, text=self.localized_strings.get("gui_fic")
        )
        self.ent_outxl_filename = Entry(self.FrOutp, width=35)
        # widgets placement
        self.lbl_outxl_filename.grid(row=0, column=1, sticky="NSWE", padx=2, pady=2)
        self.ent_outxl_filename.grid(
            row=0, column=2, columnspan=1, sticky="NSWE", padx=2, pady=2
        )
        # Frame: Progression bar
        self.FrProg = Labelframe(
            self, name="progression", text=self.localized_strings.get("gui_prog")
        )
        # variables
        self.status = StringVar(self.FrProg, "")
        self.progress = IntVar(self.FrProg, 0)
        # widgets
        self.prog_layers = Progressbar(
            self.FrProg, orient="horizontal", variable=self.progress
        )
        self.lbl_status = Label(
            master=self.FrProg, textvariable=self.status, foreground="DodgerBlue"
        )
        self.lbl_status.pack()
        # widgets placement
        self.prog_layers.pack(expand=1, fill="both")

        # miscellaneous
        misc_frame = MiscButtons(self, images_folder=self.dir_imgs)
        misc_frame.grid(row=2, rowspan=3, padx=2, pady=2, sticky="NSWE")
        # language switcher
        li_lang = [v.value for v in AvailableLocales]
        self.ddl_lang = Combobox(self, values=li_lang, width=5, state="readonly")
        self.ddl_lang.current(li_lang.index(self.def_lang))
        self.ddl_lang.bind("<<ComboboxSelected>>", self.change_lang)

        # Basic buttons
        self.val = Button(
            self,
            text=self.localized_strings.get("gui_go"),
            state=ACTIVE,
            command=lambda: self.process(),
        )
        self.can = Button(
            self,
            text=self.localized_strings.get("gui_quit"),
            command=lambda: self.destroy(),
        )

        # widgets placement
        self.welcome.grid(row=1, column=1, columnspan=1, sticky="NS", padx=2, pady=2)
        self.ddl_lang.grid(row=1, column=1, sticky="NSE", padx=2, pady=2)
        self.nb.grid(row=2, column=1)  # notebook
        self.FrProg.grid(row=3, column=1, sticky="NSWE", padx=2, pady=2)
        self.FrOutp.grid(row=4, column=1, sticky="NSWE", padx=2, pady=2)
        self.val.grid(row=5, column=1, columnspan=2, sticky="NSWE", padx=2, pady=2)
        self.can.grid(row=5, column=0, sticky="NSWE", padx=2, pady=2)

        # loading previous options
        if not self.settings.first_use:
            try:
                self.settings.load_settings(parent=self)
            except Exception as err:
                logger.error(
                    "Load settings failed: option or section is missing. Trace: {}".format(
                        err
                    )
                )

        self.ddl_lang.set(self.def_lang)
        self.change_lang(1)

        # set UI options tab
        utils_global.ui_switch(self.tab_options.opt_proxy, self.tab_options.FrOptProxy)

        # checking connection
        if not checker.check_internet_connection():
            self.nb.tab(2, state=DISABLED)
            self.nb.tab(3, state=DISABLED)

    # =================================================================================

    def change_lang(self, event):
        """Update the texts dictionary with the language selected."""
        new_lang = self.ddl_lang.get()
        # change to the new language selected
        self.localized_strings = self.txt_manager.load_texts(language_code=new_lang)
        # update widgets text
        self.welcome.config(text=self.localized_strings.get("hi") + self.uzer)
        self.can.config(text=self.localized_strings.get("gui_quit"))
        self.FrOutp.config(text=self.localized_strings.get("gui_fr4", "Output"))
        self.FrProg.config(text=self.localized_strings.get("gui_prog", "Progression"))
        self.val.config(text=self.localized_strings.get("gui_go", "Launch"))
        self.lbl_outxl_filename.config(text=self.localized_strings.get("gui_fic"))
        # tab files
        self.nb.tab(0, text=self.localized_strings.get("gui_tab1"))
        self.tab_files.FrPath.config(text=self.localized_strings.get("gui_fr1"))
        self.tab_files.FrFilters.config(text=self.localized_strings.get("gui_fr3"))
        self.tab_files.lb_target.config(text=self.localized_strings.get("gui_path"))
        self.tab_files.btn_browse.config(text=self.localized_strings.get("gui_choix"))
        # sgbd tab
        self.nb.tab(1, text=self.localized_strings.get("gui_tab2"))
        self.tab_sgbd.FrameDatabaseServicePicker.config(
            text=self.localized_strings.get("gui_fr2")
        )
        self.tab_sgbd.caz_pg_views.config(
            text=self.localized_strings.get("gui_views", "Views enabled")
        )
        self.tab_sgbd.lb_pg_services.config(
            text=self.localized_strings.get("gui_pg_service", "PG service:")
        )
        self.tab_sgbd.open_form_button.config(
            text=self.localized_strings.get("gui_database_form", "+")
        )

        # options
        self.nb.tab(2, text=self.localized_strings.get("gui_tab5"))
        self.tab_options.prox_lb_host.config(
            text=self.localized_strings.get("gui_host")
        )
        self.tab_options.prox_lb_port.config(
            text=self.localized_strings.get("gui_port")
        )
        self.tab_options.prox_lb_user.config(
            text=self.localized_strings.get("gui_user")
        )
        self.tab_options.prox_lb_password.config(
            text=self.localized_strings.get("gui_mdp")
        )
        self.tab_options.prox_lb_host.config(
            text=self.localized_strings.get("gui_host")
        )

        # credits
        self.nb.tab(3, text=self.localized_strings.get("gui_tab6"))

        # setting locale according to the language passed
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

            logger.info(f"Language switched to: {self.ddl_lang.get()}")
        except locale.Error:
            logger.error("Selected locale is not installed")

        # End of function
        return self.localized_strings

    def ligeofiles(self, target_folder: str) -> tuple[list[str]]:
        """List compatible geo-files stored into a folder structure.

        Args:
            target_folder (str): folder into walk to look for geographic datasets.

        Returns:
            tuple[list[str]]: tuple of list of paths by formats
        """
        # disable related UI items in the meanwhile
        self.tab_files.btn_browse.config(state=DISABLED)

        # Looping in folders structure
        self.status.set(self.localized_strings.get("gui_prog1"))
        self.prog_layers.start()
        logger.info(f"Begin of folders parsing: {target_folder}")

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
        ) = find_geodata_files(start_folder=target_folder)

        # end of listing
        self.prog_layers.stop()
        self.progress.set(0)

        # status message
        self.status.set(
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
                self.localized_strings.get("log_numfold"),
            )
        )

        # grouping vectors lists
        self.li_vectors.extend(self.li_shapefiles)
        self.li_vectors.extend(self.li_mapinfo_tab)
        self.li_vectors.extend(self.li_kml)
        self.li_vectors.extend(self.li_gml)
        self.li_vectors.extend(self.li_geojson)
        self.li_vectors.extend(self.li_gxt)

        # reactivating the buttons
        self.tab_files.btn_browse.config(state=ACTIVE)
        self.val.config(state=ACTIVE)
        # End of function
        return (
            self.li_shapefiles,
            self.li_mapinfo_tab,
            self.li_kml,
            self.li_gml,
            self.li_geojson,
            self.li_gxt,
            self.li_raster,
            self.li_file_database_esri,
            self.li_dxf,
            self.li_dwg,
            self.li_dgn,
            self.li_cdao,
            self.li_file_databases,
            self.li_file_database_spatialite,
        )

    def process(self):
        """Check needed info and launch different processes."""
        # get the active tab ID
        self.typo: int = self.nb.index("current")
        logger.info(f"Selected tab: {self.typo}")

        if self.typo not in (0, 1):
            logger.debug("Active tab does not allow execution.")
            return

        # saving settings
        self.settings.save_settings(self)

        # disabling UI to avoid unattended actions
        self.val.config(state=DISABLED)
        self.nb.tab(0, state=DISABLED)
        self.nb.tab(1, state=DISABLED)
        self.nb.tab(2, state=DISABLED)

        # check form fields
        if not self.check_fields(tab_data_type=self.typo):
            self.lbl_status.configure(foreground="red")
            self.val.config(state=ACTIVE)
            self.nb.tab(0, state=NORMAL)
            self.nb.tab(1, state=NORMAL)
            self.nb.tab(2, state=NORMAL)
            self.nb.select(self.typo)
            return

        # if SGBD, check connection
        if self.typo == 1:
            pg_reader = self.test_connection()
            if pg_reader is None:
                self.lbl_status.configure(foreground="red")
                self.val.config(state=ACTIVE)
                self.nb.tab(0, state=NORMAL)
                self.nb.tab(1, state=NORMAL)
                self.nb.tab(2, state=NORMAL)
                self.nb.select(self.typo)
                return

        # creating the output serializer
        self.serializer: MetadatasetSerializerXlsx = (
            MetadatasetSerializerBase.get_serializer_from_parameters(
                format_or_serializer=OutputFormats.excel,
                localized_strings=self.localized_strings,
                output_path=None,
                opt_prettify_size=self.tab_options.opt_export_size_prettify.get(),
                opt_raw_path=self.tab_options.opt_export_raw_path.get(),
            )
        )

        self.lbl_status.configure(foreground="DodgerBlue")
        self.status.set("Excel worbook object instanciated")

        # process files or PostGIS database
        if self.typo == 0:
            self.nb.select(0)
            logger.info("PROCESS LAUNCHED: files")
            self.process_files()
        elif self.typo == 1:
            self.nb.select(1)
            self.serializer.pre_serializing(has_sgbd=1)
            logger.info("PROCESS LAUNCHED: SGBD")
            # launching the process
            self.process_db(sgbd_reader=pg_reader)
        else:
            logger.critical("Unrecognized data type to process. Report it!")
        self.val.config(state=ACTIVE)
        # end of function
        return self.typo

    def process_files(self):
        """Launch the different processes."""

        # check if there are some layers into the folder structure
        if (
            len(self.li_vectors)
            + len(self.li_raster)
            + len(self.li_file_databases)
            + len(self.li_cdao)
        ):
            pass
        else:
            avert("DicoGIS - User error", self.localized_strings.get("nodata"))
            return

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
            opt_analyze_cdao=self.tab_files.opt_gxt.get(),
            opt_analyze_esri_filegdb=self.tab_files.opt_egdb.get(),
            opt_analyze_geojson=self.tab_files.opt_geoj.get(),
            opt_analyze_gml=self.tab_files.opt_gml.get(),
            opt_analyze_gxt=self.tab_files.opt_gxt.get(),
            opt_analyze_kml=self.tab_files.opt_kml.get(),
            opt_analyze_mapinfo_tab=self.tab_files.opt_tab.get(),
            opt_analyze_raster=self.tab_files.opt_rast.get(),
            opt_analyze_shapefiles=self.tab_files.opt_shp.get(),
            opt_analyze_spatialite=self.tab_files.opt_spadb.get(),
            # progress
            progress_counter=self.progress,
            progress_message_displayer=self.status,
            progress_callback_cmd=self.update,
            # misc
            opt_quick_fail=self.tab_options.opt_quick_fail.get(),
        )

        # sheets and progress bar
        total_files = geofiles_processor.count_files_to_process()
        self.prog_layers["maximum"] = total_files

        # launch processing
        geofiles_processor.process_datasets_in_queue()

        # opening and notifying
        launch(url=f"{self.serializer.output_path.resolve()}")
        send_system_notify(
            notification_title="DicoGIS analysis ended",
            notification_message=f"DicoGIS successfully processed {total_files} files. "
            "\nOpen the application to save the workbook.",
            notification_sound=self.tab_options.opt_end_process_notification_sound.get(),
        )
        self.val.config(state=ACTIVE)

    def process_db(self, sgbd_reader: ReadPostGIS):
        """Process PostGIS DB analisis.

        Args:
            sgbd_reader (ReadPostGIS): PostGIS georeader
        """
        # getting the info from shapefiles and compile it in the excel
        logger.info("Start processing PostGIS tables...")

        pg_service_name = self.tab_sgbd.ddl_pg_services.get()

        # set the default output file in UI and as serializer attribute
        self.ent_outxl_filename.delete(0, END)
        self.ent_outxl_filename.insert(
            0,
            determine_output_path(
                output_path=None, output_format="excel", pg_services=[pg_service_name]
            ),
        )
        self.serializer.output_path = Path(self.ent_outxl_filename.get())

        # setting progress bar
        self.prog_layers["maximum"] = sgbd_reader.conn.GetLayerCount()
        # parsing the layers
        for idx_layer in range(sgbd_reader.conn.GetLayerCount()):
            layer = sgbd_reader.conn.GetLayerByIndex(idx_layer)
            self.status.set(f"Reading: {layer.GetName()}")
            metadataset = sgbd_reader.infos_dataset(layer)
            logger.debug(f"Table examined: {metadataset.name}")
            self.serializer.serialize_metadaset(metadataset=metadataset)
            logger.debug(f"Layer metadata stored into workbook: {metadataset.name}")
            # increment the progress bar
            self.prog_layers["value"] = self.prog_layers["value"] + 1
            self.update()

        # saving dictionary
        self.serializer.post_serializing()

        launch(url=f"{self.serializer.output_path.resolve()}")
        send_system_notify(
            notification_title="DicoGIS analysis ended",
            notification_message="DicoGIS successfully processed "
            f"{sgbd_reader.conn.GetLayerCount()} PostGIS tables. "
            "\nOpen the application to save the workbook.",
            notification_sound=self.tab_options.opt_end_process_notification_sound.get(),
        )
        self.val.config(state=ACTIVE)

    def check_fields(self, tab_data_type: int) -> bool:
        """Check if required form fields are not empty.

        Args:
            tab_data_type: form's tab to check

        Returns:
            True if everything is OK
        """
        # error counter
        # checking empty fields
        if tab_data_type == 0:
            if not len(self.tab_files.ent_target.get()):
                avert("DicoGIS - User error", self.localized_strings.get("nofolder"))
                return False

            # check if at least a format has been choosen
            if not (
                self.tab_files.opt_shp.get()
                + self.tab_files.opt_tab.get()
                + self.tab_files.opt_kml.get()
                + self.tab_files.opt_gml.get()
                + self.tab_files.opt_geoj.get()
                + self.tab_files.opt_rast.get()
                + self.tab_files.opt_egdb.get()
                + self.tab_files.opt_dxf.get()
            ):
                avert("DicoGIS - User error", self.localized_strings.get("noformat"))
                return False

        elif tab_data_type == 1:
            if (
                self.tab_sgbd.ddl_pg_services.get() == ""
                or not self.tab_sgbd.ddl_pg_services.get()
            ):
                self.tab_sgbd.ddl_pg_services.configure(foreground="red")
                self.status.set(
                    f"PG service name is a {self.localized_strings.get('err_pg_empty_field')}"
                )
                return False

        # no error detected: let's test connection
        logger.info("Required fields are OK.")

        # End of function
        return True

    def test_connection(self) -> Optional[ReadPostGIS]:
        """Test database connection.

        Returns:
            Optional[ReadPostGIS]: PostGIS reader or None
        """
        self.dico_dataset: dict = {}

        # check if a proxy is needed
        # more information about the GDAL HTTP proxy options here:
        # http://trac.osgeo.org/gdal/wiki/ConfigOptions#GDALOGRHTTPoptions
        if self.tab_options.opt_proxy.get():
            logger.info("Proxy configured.")
            gdal.SetConfigOption(
                "GDAL_HTTP_PROXY",
                f"{self.prox_server.get()}:{self.prox_port.get()}",
            )
            if self.tab_options.opt_ntlm.get():
                # if authentication needs ...\
                # username/password or not (NTLM)
                gdal.SetConfigOption("GDAL_PROXY_AUTH", "NTLM")
                gdal.SetConfigOption("GDAL_HTTP_PROXYUSERPWD", " : ")

        else:
            logger.info("No proxy configured.")

        # testing connection settings
        sgbd_reader = ReadPostGIS(
            service=self.tab_sgbd.ddl_pg_services.get(),
            views_included=self.tab_sgbd.opt_pg_views.get(),
        )
        sgbd_reader.get_connection()

        # check connection state
        if sgbd_reader.conn is None:
            fail_reason = sgbd_reader.db_connection.state_msg
            self.status.set(f"Connection failed: {fail_reason}.")
            logger.error(f"PostGIS connection failed: {fail_reason}.")
            avert(
                title=self.localized_strings.get("err_pg_conn_fail"),
                message=fail_reason,
            )
            return None

        self.status.set(
            f"{sgbd_reader.conn.GetLayerCount()} tables found in PostGIS database."
        )

        # end of function
        return sgbd_reader


# ############################################################################
# #### Stand alone program ########
# #################################

if __name__ == "__main__":
    """standalone execution"""
    # standard
    import sys
    from os import getenv
    from tkinter import TkVersion

    # 3rd party
    # condition import
    if opersys == "linux":
        import distro

    # check Tk version
    logger.info(f"{TkVersion=}")
    if TkVersion < 8.6:
        logger.critical("DicoGIS requires Tkversion >= 8.6.")
        sys.exit(1)

    # determine theme depending on operating system and distro
    theme = "arc"
    if theme_from_env := getenv("DICOGIS_UI_THEME"):
        theme = theme_from_env
    elif opersys == "darwin":
        theme = "breeze"
    elif opersys == "linux":
        theme = "radiance"
        if distro.name().lower() == "ubuntu":
            theme = "yaru"
    elif opersys == "win32":
        theme = "breeze"
    else:
        logger.warning(
            f"Your platform/operating system is not recognized: {opersys}. "
            "It may lead to some strange behavior or buggy events."
        )

    logger.info(f"Used theme: {theme}")

    # launch the main UI
    try:
        app = DicoGIS(theme=theme)
        app.set_theme(theme_name=theme)
    except Exception as err:
        logger.critical(
            "Launching DicoGIS UI failed. Did you install the system "
            f"requirements? Trace: {err}"
        )
        raise (err)

    app.mainloop()
