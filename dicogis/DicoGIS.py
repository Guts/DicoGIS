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
from logging.handlers import RotatingFileHandler
from os import path, walk
from pathlib import Path
from sys import exit
from sys import platform as opersys
from time import strftime

# GUI
from tkinter import ACTIVE, DISABLED, END, NORMAL, Image, StringVar
from tkinter.messagebox import showerror as avert
from tkinter.messagebox import showinfo
from tkinter.ttk import (
    Button,
    Combobox,
    Entry,
    Label,
    Labelframe,
    Notebook,
    Progressbar,
)

# 3rd party
from osgeo import gdal
from ttkthemes import ThemedTk

# Project
from dicogis import __about__
from dicogis.export.md2xlsx import MetadataToXlsx
from dicogis.georeaders import (
    ReadDXF,
    ReadGDB,
    ReadGXT,
    ReadPostGIS,
    ReadRasters,
    ReadSpaDB,
    ReadVectorFlatDataset,
)
from dicogis.ui import MiscButtons, TabCredits, TabFiles, TabSettings, TabSGBD
from dicogis.utils import CheckNorris, OptionsManager, TextsManager, Utilities
from dicogis.utils.environment import get_gdal_version, get_proj_version

# ##############################################################################
# ############ Globals ############
# #################################

dir_locale = Path(__file__).parent / "locale"
txt_manager = TextsManager(dir_locale)
utils_global = Utilities()

# LOG
logger = logging.getLogger("DicoGIS")
logging.captureWarnings(True)
logger.setLevel(logging.WARNING)  # all errors will be get
log_form = logging.Formatter(
    "%(asctime)s || %(levelname)s "
    "|| %(module)s - %(lineno)d ||"
    " %(funcName)s || %(message)s"
)
logfile = RotatingFileHandler("LOG_DicoGIS.log", "a", 5000000, 1)
logfile.setLevel(logging.WARNING)
logfile.setFormatter(log_form)
logger.addHandler(logfile)

# ##############################################################################
# ############ Classes #############
# ##################################


class DicoGIS(ThemedTk):
    """Main DicoGIS GUI object.

    Args:
        ThemedTk (_type_): themed tk object.
    """

    # attributes
    package_about = __about__

    def __init__(self, theme: str = "radiance"):
        """Main window constructor
        Creates 1 frame and 2 labelled subframes"""
        logger.info(
            "\t============== {} =============".format(
                self.package_about.__title_clean__
            )
        )
        logger.info(f"Version: {self.package_about.__version__}")
        logger.info(f"GDAL: {get_gdal_version()}")
        logger.info(f"PROJ: {get_proj_version()}")

        # store vars as attr
        self.dir_locale = dir_locale
        self.dir_imgs = Path(__file__).parent / "bin/img"

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
            logger.info(f"Operating system: {platform.platform()}")
            self.iconbitmap(self.dir_imgs / "DicoGIS.ico")  # windows icon
        elif opersys.startswith("linux"):
            logger.info(f"Operating system: {platform.platform()}")
            icon = Image("photo", file=self.dir_imgs / "DicoGIS_logo.gif")
            self.call("wm", "iconphoto", self._w, icon)

        elif opersys == "darwin":
            logger.info(f"Operating system: {platform.platform()}")
        else:
            logger.warning("Operating system unknown")
            logger.info(f"Operating system: {platform.platform()}")
        self.resizable(width=False, height=False)
        self.focus_force()

        # GDAL settings
        checker.check_gdal()

        # # Variables
        # settings
        self.num_folders = 0
        self.def_rep = ""  # default folder to search for
        self.def_lang = "EN"  # default language to start
        self.today = strftime("%Y-%m-%d")  # date of the day
        li_lang = [lg.name[5:-4] for lg in dir_locale.glob("*.xml")]  # languages
        self.blabla = {}  # texts dictionary

        # formats / type: vectors
        self.li_vectors_formats = (
            ".shp",
            ".tab",
            ".kml",
            ".gml",
            ".geojson",
        )  # vectors handled
        self.li_shp = []  # list for shapefiles path
        self.li_tab = []  # list for MapInfo tables path
        self.li_kml = []  # list for KML path
        self.li_gml = []  # list for GML path
        self.li_geoj = []  # list for GeoJSON paths
        self.li_gxt = []  # list for GXT paths
        self.li_vectors = []  # list for all vectors
        # formats / type: rasters
        self.li_raster = []  # list for rasters paths
        self.li_raster_formats = (".ecw", ".tif", ".jp2")  # raster handled
        # formats / type: file databases
        self.li_fdb = []  # list for all files databases
        self.li_egdb = []  # list for Esri File Geodatabases
        self.li_spadb = []  # list for Spatialite Geodatabases
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

        # Notebook
        self.nb = Notebook(self)
        # tabs
        self.tab_files = TabFiles(self.nb, self.blabla)  # tab_id = 0
        self.tab_sgbd = TabSGBD(self.nb)  # tab_id = 1
        self.tab_options = TabSettings(
            self.nb, self.blabla, utils_global.ui_switch
        )  # tab_id = 2
        self.tab_credits = TabCredits(
            self.nb, self.blabla, utils_global.ui_switch
        )  # tab_id = 3

        # fillfulling text
        txt_manager.load_texts(dico_texts=self.blabla, lang=self.def_lang)

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
            self, text=self.blabla.get("hi") + self.uzer, foreground="blue"
        )

        # Frame: Output
        self.FrOutp = Labelframe(self, name="output", text=self.blabla.get("gui_fr4"))
        # widgets
        self.lbl_outxl_filename = Label(self.FrOutp, text=self.blabla.get("gui_fic"))
        self.ent_outxl_filename = Entry(self.FrOutp, width=35)
        # widgets placement
        self.lbl_outxl_filename.grid(row=0, column=1, sticky="NSWE", padx=2, pady=2)
        self.ent_outxl_filename.grid(
            row=0, column=2, columnspan=1, sticky="NSWE", padx=2, pady=2
        )
        # Frame: Progression bar
        self.FrProg = Labelframe(
            self, name="progression", text=self.blabla.get("gui_prog")
        )
        # variables
        self.status = StringVar(self.FrProg, "")
        # widgets
        self.prog_layers = Progressbar(self.FrProg, orient="horizontal")
        Label(
            master=self.FrProg, textvariable=self.status, foreground="DodgerBlue"
        ).pack()
        # widgets placement
        self.prog_layers.pack(expand=1, fill="both")

        # miscellaneous
        misc_frame = MiscButtons(self, images_folder=self.dir_imgs)
        misc_frame.grid(row=2, rowspan=3, padx=2, pady=2, sticky="NSWE")
        # language switcher
        self.ddl_lang = Combobox(self, values=li_lang, width=5)
        self.ddl_lang.current(li_lang.index(self.def_lang))
        self.ddl_lang.bind("<<ComboboxSelected>>", self.change_lang)

        # Basic buttons
        self.val = Button(
            self,
            text=self.blabla.get("gui_go"),
            state=ACTIVE,
            command=lambda: self.process(),
        )
        self.can = Button(
            self, text=self.blabla.get("gui_quit"), command=lambda: self.destroy()
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
        else:
            pass
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
        txt_manager.load_texts(dico_texts=self.blabla, lang=new_lang)
        # update widgets text
        self.welcome.config(text=self.blabla.get("hi") + self.uzer)
        self.can.config(text=self.blabla.get("gui_quit"))
        self.FrOutp.config(text=self.blabla.get("gui_fr4", "Output"))
        self.FrProg.config(text=self.blabla.get("gui_prog", "Progression"))
        self.val.config(text=self.blabla.get("gui_go", "Launch"))
        self.lbl_outxl_filename.config(text=self.blabla.get("gui_fic"))
        # tab files
        self.nb.tab(0, text=self.blabla.get("gui_tab1"))
        self.tab_files.FrPath.config(text=self.blabla.get("gui_fr1"))
        self.tab_files.FrFilters.config(text=self.blabla.get("gui_fr3"))
        self.tab_files.lb_target.config(text=self.blabla.get("gui_path"))
        self.tab_files.btn_browse.config(text=self.blabla.get("gui_choix"))
        # sgbd tab
        self.nb.tab(1, text=self.blabla.get("gui_tab2"))
        self.tab_sgbd.FrDb.config(text=self.blabla.get("gui_fr2"))
        self.tab_sgbd.lb_H.config(text=self.blabla.get("gui_host"))
        self.tab_sgbd.lb_P.config(text=self.blabla.get("gui_port"))
        self.tab_sgbd.lb_D.config(text=self.blabla.get("gui_db"))
        self.tab_sgbd.lb_U.config(text=self.blabla.get("gui_user"))
        self.tab_sgbd.lb_M.config(text=self.blabla.get("gui_mdp"))

        # options
        self.nb.tab(2, text=self.blabla.get("gui_tab5"))
        self.tab_options.prox_lb_H.config(text=self.blabla.get("gui_host"))
        self.tab_options.prox_lb_P.config(text=self.blabla.get("gui_port"))
        self.tab_options.prox_lb_M.config(text=self.blabla.get("gui_mdp"))
        self.tab_options.prox_lb_H.config(text=self.blabla.get("gui_host"))

        # credits
        self.nb.tab(3, text=self.blabla.get("gui_tab6"))

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
        return self.blabla

    def ligeofiles(self, foldertarget):
        """List compatible geo-files stored into a folder structure."""
        # reseting global variables
        self.li_shp = []
        self.li_tab = []
        self.li_kml = []
        self.li_gml = []
        self.li_geoj = []
        self.li_gxt = []
        self.li_vectors = []
        self.li_dxf = []
        self.li_dwg = []
        self.li_dgn = []
        self.li_cdao = []
        self.li_raster = []
        self.li_fdb = []
        self.li_egdb = []
        self.li_spadb = []
        self.tab_files.btn_browse.config(state=DISABLED)

        # Looping in folders structure
        self.status.set(self.blabla.get("gui_prog1"))
        self.prog_layers.start()
        logger.info(f"Begin of folders parsing: {foldertarget}")
        for root, dirs, files in walk(foldertarget):
            self.num_folders = self.num_folders + len(dirs)
            for d in dirs:
                """looking for File Geodatabase among directories"""
                try:
                    path.join(root, d)
                    full_path = path.join(root, d)
                except UnicodeDecodeError:
                    full_path = path.join(root, d.decode("latin1"))
                if full_path[-4:].lower() == ".gdb":
                    # add complete path of Esri FileGeoDatabase
                    self.li_egdb.append(path.abspath(full_path))
                else:
                    pass
            for f in files:
                """looking for files with geographic data"""
                try:
                    path.join(root, f)
                    full_path = path.join(root, f)
                except UnicodeDecodeError:
                    full_path = path.join(root, f.decode("latin1"))
                # Looping on files contained
                if (
                    path.splitext(full_path.lower())[1].lower() == ".shp"
                    and (
                        path.isfile(f"{full_path[:-4]}.dbf")
                        or path.isfile(f"{full_path[:-4]}.DBF")
                    )
                    and (
                        path.isfile(f"{full_path[:-4]}.shx")
                        or path.isfile(f"{full_path[:-4]}.SHX")
                    )
                ):
                    """listing compatible shapefiles"""
                    # add complete path of shapefile
                    self.li_shp.append(full_path)
                elif (
                    path.splitext(full_path.lower())[1] == ".tab"
                    and (
                        path.isfile(full_path[:-4] + ".dat")
                        or path.isfile(full_path[:-4] + ".DAT")
                    )
                    and (
                        path.isfile(full_path[:-4] + ".map")
                        or path.isfile(full_path[:-4] + ".MAP")
                    )
                    and (
                        path.isfile(full_path[:-4] + ".id")
                        or path.isfile(full_path[:-4] + ".ID")
                    )
                ):
                    """listing MapInfo tables"""
                    # add complete path of MapInfo file
                    self.li_tab.append(full_path)
                elif (
                    path.splitext(full_path.lower())[1] == ".kml"
                    or path.splitext(full_path.lower())[1] == ".kmz"
                ):
                    """listing KML and KMZ"""
                    # add complete path of KML file
                    self.li_kml.append(full_path)
                elif path.splitext(full_path.lower())[1] == ".gml":
                    """listing GML"""
                    # add complete path of GML file
                    self.li_gml.append(full_path)
                elif path.splitext(full_path.lower())[1] == ".geojson":
                    """listing GeoJSON"""
                    # add complete path of GeoJSON file
                    self.li_geoj.append(full_path)
                elif path.splitext(full_path.lower())[1] == ".gxt":
                    """listing Geoconcept eXport Text (GXT)"""
                    # add complete path of GXT file
                    self.li_gxt.append(full_path)
                elif path.splitext(full_path.lower())[1] in self.li_raster_formats:
                    """listing compatible rasters"""
                    # add complete path of raster file
                    self.li_raster.append(full_path)
                elif path.splitext(full_path.lower())[1] == ".dxf":
                    """listing DXF"""
                    # add complete path of DXF file
                    self.li_dxf.append(full_path)
                elif path.splitext(full_path.lower())[1] == ".dwg":
                    """listing DWG"""
                    # add complete path of DWG file
                    self.li_dwg.append(full_path)
                elif path.splitext(full_path.lower())[1] == ".dgn":
                    """listing MicroStation DGN"""
                    # add complete path of DGN file
                    self.li_dgn.append(full_path)
                elif path.splitext(full_path.lower())[1] == ".sqlite":
                    """listing Spatialite DB"""
                    # add complete path of DGN file
                    self.li_spadb.append(full_path)
                else:
                    continue

        # grouping CAO/DAO files
        self.li_cdao.extend(self.li_dxf)
        self.li_cdao.extend(self.li_dwg)
        self.li_cdao.extend(self.li_dgn)
        # grouping File geodatabases
        self.li_fdb.extend(self.li_egdb)
        self.li_fdb.extend(self.li_spadb)

        # end of listing
        self.prog_layers.stop()
        logger.info(
            "End of folders parsing: {} shapefiles - "
            "{} tables (MapInfo) - "
            "{} KML - "
            "{} GML - "
            "{} GeoJSON"
            "{} rasters - "
            "{} Esri FileGDB - "
            "{} Spatialite - "
            "{} CAO/DAO - "
            "{} GXT - in {}{}".format(
                len(self.li_shp),
                len(self.li_tab),
                len(self.li_kml),
                len(self.li_gml),
                len(self.li_geoj),
                len(self.li_raster),
                len(self.li_egdb),
                len(self.li_spadb),
                len(self.li_cdao),
                len(self.li_gxt),
                self.num_folders,
                self.blabla.get("log_numfold"),
            )
        )
        # grouping vectors lists
        self.li_vectors.extend(self.li_shp)
        self.li_vectors.extend(self.li_tab)
        self.li_vectors.extend(self.li_kml)
        self.li_vectors.extend(self.li_gml)
        self.li_vectors.extend(self.li_geoj)
        self.li_vectors.extend(self.li_gxt)

        # Lists ordering and tupling
        self.li_shp.sort()
        self.li_shp = tuple(self.li_shp)
        self.li_tab.sort()
        self.li_tab = tuple(self.li_tab)
        self.li_raster.sort()
        self.li_raster = tuple(self.li_raster)
        self.li_kml.sort()
        self.li_kml = tuple(self.li_kml)
        self.li_gml.sort()
        self.li_gml = tuple(self.li_gml)
        self.li_geoj.sort()
        self.li_geoj = tuple(self.li_geoj)
        self.li_gxt.sort()
        self.li_gxt = tuple(self.li_gxt)
        self.li_egdb.sort()
        self.li_egdb = tuple(self.li_egdb)
        self.li_spadb.sort()
        self.li_spadb = tuple(self.li_spadb)
        self.li_fdb.sort()
        self.li_fdb = tuple(self.li_fdb)
        self.li_dxf.sort()
        self.li_dxf = tuple(self.li_dxf)
        self.li_dwg.sort()
        self.li_dwg = tuple(self.li_dwg)
        self.li_dgn.sort()
        self.li_dgn = tuple(self.li_dgn)
        self.li_cdao.sort()
        self.li_cdao = tuple(self.li_cdao)

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
                len(self.li_shp),
                len(self.li_tab),
                len(self.li_kml),
                len(self.li_gml),
                len(self.li_geoj),
                len(self.li_gxt),
                len(self.li_raster),
                len(self.li_fdb),
                len(self.li_cdao),
                self.num_folders,
                self.blabla.get("log_numfold"),
            )
        )

        # reactivating the buttons
        self.tab_files.btn_browse.config(state=ACTIVE)
        self.val.config(state=ACTIVE)
        # End of function
        return (
            foldertarget,
            self.li_shp,
            self.li_tab,
            self.li_kml,
            self.li_gml,
            self.li_geoj,
            self.li_gxt,
            self.li_raster,
            self.li_egdb,
            self.li_dxf,
            self.li_dwg,
            self.li_dgn,
            self.li_cdao,
            self.li_fdb,
            self.li_spadb,
        )

    def process(self):
        """Check needed info and launch different processes."""
        # saving settings
        self.settings.save_settings(self)

        # get the active tab ID
        self.typo: int = self.nb.index("current")
        logger.info(f"Selected tab: {self.typo}")

        # disabling UI to avoid unattended actions
        self.val.config(state=DISABLED)
        self.nb.tab(0, state=DISABLED)
        self.nb.tab(1, state=DISABLED)
        self.nb.tab(2, state=DISABLED)

        if not self.check_fields(tab_data_type=self.typo):
            self.val.config(state=ACTIVE)
            self.nb.tab(0, state=NORMAL)
            self.nb.tab(1, state=NORMAL)
            self.nb.tab(2, state=NORMAL)
            return

        # creating the Excel workbook
        self.wb = MetadataToXlsx(
            texts=self.blabla,
            opt_size_prettify=self.tab_options.opt_export_size_prettify.get(),
        )
        logger.info("Excel file created")

        # process files or PostGIS database
        if self.typo == 0:
            self.nb.select(0)
            logger.info("PROCESS LAUNCHED: files")
            self.process_files()
        elif self.typo == 1:
            self.nb.select(1)
            self.wb.set_worksheets(has_sgbd=1)
            logger.info("PROCESS LAUNCHED: SGBD")
            self.check_fields(tab_data_type=self.typo)
        elif self.typo == 2:
            self.nb.select(2)
            logger.info("PROCESS LAUNCHED: services")
            # self.check_fields(tab_data_type=self.typo)
        else:
            pass
        self.val.config(state=ACTIVE)
        # end of function
        return self.typo

    def process_files(self):
        """Launch the different processes."""

        # check if there are some layers into the folder structure
        if (
            len(self.li_vectors)
            + len(self.li_raster)
            + len(self.li_fdb)
            + len(self.li_cdao)
        ):
            pass
        else:
            avert("DicoGIS - User error", self.blabla.get("nodata"))
            return
        # georeaders
        georeader_vector = ReadVectorFlatDataset()
        georeader_egdb = ReadGDB()

        # sheets and progress bar
        total_files = 0
        if self.tab_files.opt_shp.get() and len(self.li_shp):
            total_files += len(self.li_shp)
            self.wb.set_worksheets(has_vector=1)
        else:
            pass
        if self.tab_files.opt_tab.get() and len(self.li_tab):
            total_files += len(self.li_tab)
            self.wb.set_worksheets(has_vector=1)
        else:
            pass
        if self.tab_files.opt_kml.get() and len(self.li_kml):
            total_files += len(self.li_kml)
            self.wb.set_worksheets(has_vector=1)
        else:
            pass
        if self.tab_files.opt_gml.get() and len(self.li_gml):
            total_files += len(self.li_gml)
            self.wb.set_worksheets(has_vector=1)
        else:
            pass
        if self.tab_files.opt_geoj.get() and len(self.li_geoj):
            total_files += len(self.li_geoj)
            self.wb.set_worksheets(has_vector=1)
        else:
            pass
        if self.tab_files.opt_gxt.get() and len(self.li_gxt):
            total_files += len(self.li_gxt)
            self.wb.set_worksheets(has_vector=1)
        else:
            pass
        if self.tab_files.opt_rast.get() and len(self.li_raster):
            total_files += len(self.li_raster)
            self.wb.set_worksheets(has_raster=1)
        else:
            pass
        if self.tab_files.opt_egdb.get() and len(self.li_egdb):
            total_files += len(self.li_egdb)
            self.wb.set_worksheets(has_filedb=1)
        else:
            pass
        if self.tab_files.opt_spadb.get() and len(self.li_spadb):
            total_files += len(self.li_spadb)
            self.wb.set_worksheets(has_filedb=1)
        else:
            pass
        if self.tab_files.opt_dxf.get() and len(self.li_cdao):
            total_files += len(self.li_cdao)
            self.wb.set_worksheets(has_cad=1)
        else:
            pass

        self.prog_layers["maximum"] = total_files
        self.prog_layers["value"]

        if self.tab_files.opt_shp.get() and len(self.li_shp) > 0:
            logger.info("Processing shapefiles: start")
            for shp in self.li_shp:
                """looping on shapefiles list"""
                self.status.set(path.basename(shp))
                logger.info(f"Processing: {shp}")
                # increment the progress bar
                self.prog_layers["value"] = self.prog_layers["value"] + 1
                self.update()
                # reset recipient data
                self.dico_layer.clear()
                # getting the informations
                try:
                    georeader_vector.infos_dataset(
                        path.abspath(shp), self.dico_layer, self.blabla
                    )
                    logger.debug("Dataset metadata extracted")
                except (AttributeError, RuntimeError, Exception) as err:
                    """empty files"""
                    logger.error(
                        "Metadata extraction failed on dataset: {}. Trace: {}".format(
                            shp, err
                        )
                    )
                    self.prog_layers["value"] = self.prog_layers["value"] + 1
                    continue
                # writing to the Excel dictionary
                self.wb.store_md_vector(self.dico_layer)

                logger.debug("Layer metadata stored into workbook.")
        else:
            if len(self.li_shp):
                logger.info(f"Ignoring {len(self.li_shp)} shapefiles")
            pass

        if self.tab_files.opt_tab.get() and len(self.li_tab) > 0:
            logger.info("Processing MapInfo tables: start")
            for tab in self.li_tab:
                """looping on MapInfo tables list"""
                self.status.set(path.basename(tab))
                logger.info(tab)
                # increment the progress bar
                self.prog_layers["value"] = self.prog_layers["value"] + 1
                self.update()
                # reset recipient data
                self.dico_layer.clear()
                # getting the informations
                try:
                    georeader_vector.infos_dataset(
                        path.abspath(tab), self.dico_layer, self.blabla
                    )
                    logger.debug("Dataset metadata extracted")
                except (AttributeError, RuntimeError, Exception) as err:
                    """empty files"""
                    logger.error(
                        "Metadata extraction failed on dataset: {}. Trace: {}".format(
                            tab, err
                        )
                    )
                    self.prog_layers["value"] = self.prog_layers["value"] + 1
                    continue
                # writing to the Excel file
                self.wb.store_md_vector(self.dico_layer)

                logger.debug("Layer metadata stored into workbook.")
        else:
            if len(self.li_tab):
                logger.info(f"Ignoring {len(self.li_tab)} MapInfo tables")

        if self.tab_files.opt_kml.get() and len(self.li_kml) > 0:
            logger.info("Processing KML-KMZ: start")
            for kml in self.li_kml:
                """looping on KML/KMZ list"""
                self.status.set(path.basename(kml))
                logger.info(kml)
                # increment the progress bar
                self.prog_layers["value"] = self.prog_layers["value"] + 1
                self.update()
                # reset recipient data
                self.dico_layer.clear()
                self.dico_fields.clear()
                # getting the informations
                try:
                    georeader_vector.infos_dataset(
                        path.abspath(kml), self.dico_layer, self.blabla
                    )
                    logger.debug("Dataset metadata extracted")
                except (AttributeError, RuntimeError, Exception) as err:
                    """empty files"""
                    logger.error(
                        "Metadata extraction failed on dataset: {}. Trace: {}".format(
                            kml, err
                        )
                    )
                    self.prog_layers["value"] = self.prog_layers["value"] + 1
                    continue
                # writing to the Excel dictionary
                self.wb.store_md_vector(self.dico_layer)
                logger.debug("Layer metadata stored into workbook.")
        else:
            if len(self.li_kml):
                logger.info(f"Ignoring {len(self.li_kml)} KML")

        if self.tab_files.opt_gml.get() and len(self.li_gml) > 0:
            logger.info("Processing GML: start")
            for gml in self.li_gml:
                """looping on GML list"""
                self.status.set(path.basename(gml))
                logger.info(gml)
                # increment the progress bar
                self.prog_layers["value"] = self.prog_layers["value"] + 1
                self.update()
                # reset recipient data
                self.dico_layer.clear()
                self.dico_fields.clear()
                # getting the informations
                try:
                    georeader_vector.infos_dataset(
                        path.abspath(gml), self.dico_layer, self.blabla
                    )
                    logger.debug("Dataset metadata extracted")
                except (AttributeError, RuntimeError, Exception) as err:
                    """empty files"""
                    logger.error(
                        "Metadata extraction failed on dataset: {}. Trace: {}".format(
                            gml, err
                        )
                    )
                    self.prog_layers["value"] = self.prog_layers["value"] + 1
                    continue
                # writing to the Excel dictionary
                self.wb.store_md_vector(self.dico_layer)
                logger.debug("Layer metadata stored into workbook.")
        else:
            if len(self.li_gml):
                logger.info(f"Ignoring {len(self.li_gml)} GML")

        if self.tab_files.opt_geoj.get() and len(self.li_geoj) > 0:
            logger.info("Processing GeoJSON: start")
            for geojson in self.li_geoj:
                """looping on GeoJSON list"""
                self.status.set(path.basename(geojson))
                logger.info(geojson)
                # increment the progress bar
                self.prog_layers["value"] = self.prog_layers["value"] + 1
                self.update()
                # reset recipient data
                self.dico_layer.clear()
                self.dico_fields.clear()
                # getting the informations
                try:
                    georeader_vector.infos_dataset(
                        path.abspath(geojson), self.dico_layer, self.blabla
                    )
                    logger.debug("Dataset metadata extracted")
                except (AttributeError, RuntimeError, Exception) as err:
                    """empty files"""
                    logger.error(
                        "Metadata extraction failed on dataset: {}. Trace: {}".format(
                            geojson, err
                        )
                    )
                    self.prog_layers["value"] = self.prog_layers["value"] + 1
                    continue
                # writing to the Excel dictionary
                self.wb.store_md_vector(self.dico_layer)
                logger.debug("Layer metadata stored into workbook.")
        else:
            if len(self.li_geoj):
                logger.info(f"Ignoring {len(self.li_geoj)} GeoJSON")

        if self.tab_files.opt_gxt.get() and len(self.li_gxt) > 0:
            logger.info("Processing GXT: start")
            for gxtpath in self.li_gxt:
                """looping on gxt list"""
                self.status.set(path.basename(gxtpath))
                logger.info(gxtpath)
                # increment the progress bar
                self.prog_layers["value"] = self.prog_layers["value"] + 1
                self.update()
                # reset recipient data
                self.dico_layer.clear()
                self.dico_fields.clear()
                # getting the informations
                try:
                    ReadGXT(
                        path.abspath(gxtpath),
                        self.dico_layer,
                        "Geoconcept eXport Text",
                        self.blabla,
                    )
                    logger.debug("Dataset metadata extracted")
                except (AttributeError, RuntimeError, Exception) as err:
                    """empty files"""
                    logger.error(
                        "Metadata extraction failed on dataset: {}. Trace: {}".format(
                            gxtpath, err
                        )
                    )
                    self.prog_layers["value"] = self.prog_layers["value"] + 1
                    continue
                # writing to the Excel dictionary
                self.wb.store_md_vector(self.dico_layer)
                logger.debug("Layer metadata stored into workbook.")
        else:
            if len(self.li_gxt):
                logger.info(f"Ignoring {len(self.li_gxt)} Geoconcept eXport Text")

        if self.tab_files.opt_rast.get() and len(self.li_raster) > 0:
            logger.info("Processing rasters: start")
            for raster in self.li_raster:
                """looping on rasters list"""
                self.status.set(path.basename(raster))
                logger.info(raster)
                # increment the progress bar
                self.prog_layers["value"] = self.prog_layers["value"] + 1
                self.update()
                # reset recipient data
                self.dico_raster.clear()
                self.dico_bands.clear()
                # getting the informations
                try:
                    ReadRasters(
                        path.abspath(raster),
                        self.dico_raster,
                        self.dico_bands,
                        path.splitext(raster)[1],
                        self.blabla,
                    )
                    logger.debug("Dataset metadata extracted")
                except (AttributeError, RuntimeError, Exception) as err:
                    """empty files"""
                    logger.error(
                        "Metadata extraction failed on dataset: {}. Trace: {}".format(
                            raster, err
                        )
                    )
                    self.prog_layers["value"] = self.prog_layers["value"] + 1
                    continue
                # writing to the Excel dictionary
                self.wb.store_md_raster(self.dico_raster, self.dico_bands)
                logger.debug("Layer metadata stored into workbook.")
        else:
            if len(self.li_raster):
                logger.info(f"Ignoring {len(self.li_raster)} rasters")

        if self.tab_files.opt_egdb.get() and len(self.li_egdb) > 0:
            logger.info("Processing Esri FileGDB: start")
            for gdb in self.li_egdb:
                """looping on FileGDB list"""
                self.status.set(path.basename(gdb))
                logger.info(gdb)
                # increment the progress bar
                self.prog_layers["value"] = self.prog_layers["value"] + 1
                self.update()
                # reset recipient data
                self.dico_fdb.clear()
                self.dico_fields.clear()
                # getting the informations
                try:
                    georeader_egdb.infos_dataset(
                        path.abspath(gdb),
                        self.dico_fdb,
                        self.blabla,
                        tipo="Esri FileGDB",
                    )
                    logger.debug("Dataset metadata extracted")
                except (AttributeError, RuntimeError, Exception) as err:
                    """empty files"""
                    logger.error(
                        "Metadata extraction failed on dataset: {}. Trace: {}".format(
                            gdb, err
                        )
                    )
                    self.prog_layers["value"] = self.prog_layers["value"] + 1
                    continue
                # writing to the Excel dictionary
                self.wb.store_md_fdb(self.dico_fdb)
                logger.debug("Layer metadata stored into workbook.")
        else:
            if len(self.li_egdb):
                logger.info(f"Ignoring {len(self.li_egdb)} Esri FileGDB")

        if self.tab_files.opt_spadb.get() and len(self.li_spadb) > 0:
            logger.info("Processing Spatialite DB: start")
            for spadb in self.li_spadb:
                """looping on Spatialite DBs list"""
                self.status.set(path.basename(spadb))
                logger.info(spadb)
                # increment the progress bar
                self.prog_layers["value"] = self.prog_layers["value"] + 1
                self.update()
                # reset recipient data
                self.dico_fdb.clear()
                self.dico_fields.clear()
                # getting the informations
                try:
                    ReadSpaDB(
                        path.abspath(spadb), self.dico_fdb, "Spatialite", self.blabla
                    )
                    logger.debug("Dataset metadata extracted")
                except (AttributeError, RuntimeError, Exception) as err:
                    """empty files"""
                    logger.error(
                        "Metadata extraction failed on dataset: {}. Trace: {}".format(
                            spadb, err
                        )
                    )
                    self.prog_layers["value"] = self.prog_layers["value"] + 1
                    continue
                # writing to the Excel dictionary
                self.wb.store_md_fdb(self.dico_fdb)
                logger.debug("Layer metadata stored into workbook.")
        else:
            if len(self.li_spadb):
                logger.info(f"Ignoring {len(self.li_spadb)} Spatialite DB")

        if self.tab_files.opt_dxf.get() and len(self.li_cdao) > 0:
            logger.info("Processing CAO/DAO: start")
            for dxf in self.li_dxf:
                """looping on DXF list"""
                self.status.set(path.basename(dxf))
                logger.info(dxf)
                # increment the progress bar
                self.prog_layers["value"] = self.prog_layers["value"] + 1
                self.update()
                # reset recipient data
                self.dico_cdao.clear()
                # getting the informations
                try:
                    ReadDXF(
                        path.abspath(dxf), self.dico_cdao, "AutoCAD DXF", self.blabla
                    )
                    logger.debug("Dataset metadata extracted")
                except (AttributeError, RuntimeError, Exception) as err:
                    """empty files"""
                    logger.error(
                        "Metadata extraction failed on dataset: {}. Trace: {}".format(
                            dxf, err
                        )
                    )
                    self.prog_layers["value"] = self.prog_layers["value"] + 1
                    continue
                # writing to the Excel dictionary
                self.wb.store_md_cad(self.dico_cdao)
                logger.debug("Layer metadata stored into workbook.")
        else:
            if len(self.li_cdao):
                logger.info(f"Ignoring {len(self.li_cdao)} CAO/DAO files")

        # saving dictionary
        self.bell()
        self.val.config(state=ACTIVE)
        self.wb.tunning_worksheets()
        saved = utils_global.safe_save(
            wb=self.wb,
            dest_dir=self.tab_files.target_path.get(),
            dest_filename=self.ent_outxl_filename.get(),
            ftype="Excel Workbook",
            dlg_title=self.blabla.get("gui_excel"),
        )
        logger.info("Workbook saved: %s", self.ent_outxl_filename.get())

        # quit and exit
        if saved is not None:
            utils_global.open_dir_file(saved[1])
        else:
            showinfo(
                title=self.blabla.get(
                    "no_output_file_selected", "No output file selected"
                ),
                message=self.blabla.get(
                    "no_output_file_selected", "Dictionary has not been saved."
                ),
            )

    def process_db(self, sgbd_reader):
        """Process PostGIS DB analisis."""
        # getting the info from shapefiles and compile it in the excel
        logger.info("PostGIS table processing...")
        # setting progress bar
        self.prog_layers["maximum"] = sgbd_reader.conn.GetLayerCount()
        # parsing the layers
        for layer in sgbd_reader.conn:
            # reset recipient data
            self.dico_dataset.clear()
            sgbd_reader.infos_dataset(layer)
            logger.info(f"Table examined: {layer.GetName()}")
            self.wb.store_md_sgdb(self.dico_dataset)
            logger.debug("Layer metadata stored into workbook.")
            # increment the progress bar
            self.prog_layers["value"] = self.prog_layers["value"] + 1
            self.update()

        # saving dictionary
        self.bell()
        self.val.config(state=ACTIVE)
        self.wb.tunning_worksheets()
        saved = utils_global.safe_save(
            wb=self.wb,
            dest_filename=self.ent_outxl_filename.get(),
            ftype="Excel Workbook",
            dlg_title=self.blabla.get("gui_excel"),
        )
        logger.info(
            f"Workbook saved: {self.ent_outxl_filename.get()}",
        )

        # quit and exit
        utils_global.open_dir_file(saved[1])
        self.destroy()
        exit()

    def check_fields(self, tab_data_type: int) -> bool:
        """Check if required fields are not empty"""
        # error counter
        # checking empty fields
        if tab_data_type == 0:
            if not len(self.tab_files.ent_target.get()):
                avert("DicoGIS - User error", self.blabla.get("nofolder"))
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
                avert("DicoGIS - User error", self.blabla.get("noformat"))
                return False

        elif tab_data_type == 1:
            if (
                self.tab_sgbd.host.get() == ""
                or self.tab_sgbd.host.get() == self.blabla.get("err_pg_empty_field")
            ):
                self.tab_sgbd.ent_H.configure(foreground="red")
                self.tab_sgbd.ent_H.delete(0, END)
                self.tab_sgbd.ent_H.insert(0, self.blabla.get("err_pg_empty_field"))
                return
            else:
                pass
            if not self.tab_sgbd.ent_P.get():
                self.tab_sgbd.ent_P.configure(foreground="red")
                self.tab_sgbd.ent_P.delete(0, END)
                self.tab_sgbd.ent_P.insert(0, 0000)
                return
            else:
                pass
            if (
                self.tab_sgbd.dbnb.get() == ""
                or self.tab_sgbd.host.get() == self.blabla.get("err_pg_empty_field")
            ):
                self.tab_sgbd.ent_D.configure(foreground="red")
                self.tab_sgbd.ent_D.delete(0, END)
                self.tab_sgbd.ent_D.insert(0, self.blabla.get("err_pg_empty_field"))
                return
            else:
                pass
            if (
                self.tab_sgbd.user.get() == ""
                or self.tab_sgbd.host.get() == self.blabla.get("err_pg_empty_field")
            ):
                self.tab_sgbd.ent_U.configure(foreground="red")
                self.tab_sgbd.ent_U.delete(0, END)
                self.tab_sgbd.ent_U.insert(0, self.blabla.get("err_pg_empty_field"))
                return
            else:
                pass
            if (
                self.tab_sgbd.pswd.get() == ""
                or self.tab_sgbd.pswd.get() == self.blabla.get("err_pg_empty_field")
            ):
                self.tab_sgbd.ent_M.configure(foreground="red")
                self.tab_sgbd.ent_M.delete(0, END)
                self.tab_sgbd.ent_M.insert(0, self.blabla.get("err_pg_empty_field"))
                return
            else:
                pass
        # no error detected: let's test connection
        logger.info("Required fields are OK.")

        if tab_data_type == 1:
            self.test_connection()
        # End of function
        return True

    def test_connection(self):
        """Test database connection and handling specific
        settings : proxy, DB views, etc.
        """
        self.dico_dataset = {}
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
                pass
        else:
            logger.info("No proxy configured.")

        # testing connection settings
        sgbd_reader = ReadPostGIS(
            host=self.tab_sgbd.host.get(),
            port=self.tab_sgbd.port.get(),
            db_name=self.tab_sgbd.dbnb.get(),
            user=self.tab_sgbd.user.get(),
            password=self.tab_sgbd.pswd.get(),
            views_included=self.tab_sgbd.opt_pgvw.get(),
            dico_dataset=self.dico_dataset,
            txt=self.blabla,
        )

        # check connection state
        if not sgbd_reader.conn:
            fail_reason = self.dico_dataset.get("conn_state")
            self.status.set(f"Connection failed: {fail_reason}.")
            avert(title=self.blabla.get("err_pg_conn_fail"), message=fail_reason)
            return None
        else:
            # connection succeeded
            pass

        self.status.set(f"{len(sgbd_reader.conn)} tables")
        # set the default output file
        self.ent_outxl_filename.delete(0, END)
        self.ent_outxl_filename.insert(
            0,
            "DicoGIS_{}-{}_{}.xlsx".format(
                self.tab_sgbd.dbnb.get(), self.tab_sgbd.host.get(), self.today
            ),
        )
        # launching the process
        self.process_db(sgbd_reader)
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
