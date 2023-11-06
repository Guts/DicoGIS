#! python3  # noqa: E265


"""
    Name:         TabFiles
    Purpose:      Tab containing files widgets in DicoGIS Notebook.

    Author:       Julien Moura (@geojulien)
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

import gettext
import logging
import threading
from os import path

# Standard library
from pathlib import Path
from time import strftime

# GUI
from tkinter import END, IntVar, StringVar, Tk
from tkinter.filedialog import askdirectory
from tkinter.messagebox import showinfo
from tkinter.ttk import Button, Checkbutton, Entry, Frame, Label, Labelframe

# ##############################################################################
# ############ Globals ############
# #################################

_ = gettext.gettext
today = strftime("%Y-%m-%d")
logger = logging.getLogger(__name__)  # LOG

# ##############################################################################
# ########## Classes ###############
# ##################################


class TabFiles(Frame):
    def __init__(self, parent, txt: dict = {}):
        """Instanciating the output workbook."""
        self.p = parent
        self.txt = txt
        Frame.__init__(self)

        # -- VARIABLES -------------------------------------------------------
        self.target_path = StringVar()
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
        # formats / type: maps documents
        self.li_mapdocs = []  # list for all map & documents
        self.li_qgs = []  # list for QGS path

        # -- Source path -----------------------------------------------------
        self.FrPath = Labelframe(self, name="files", text=txt.get("gui_fr1", "Path"))

        # target folder
        self.lb_target = Label(self.FrPath, text=txt.get("gui_path"))
        self.ent_target = Entry(
            master=self.FrPath, width=35, textvariable=self.target_path
        )
        self.btn_browse = Button(
            self.FrPath,
            text="\U0001F3AF " + txt.get("gui_choix", "Browse"),
            command=lambda: self.get_target_path(r"."),
            takefocus=True,
        )
        self.btn_browse.focus_force()

        # widgets placement
        self.lb_target.grid(
            row=1, column=1, columnspan=1, sticky="NSWE", padx=2, pady=2
        )
        self.ent_target.grid(
            row=1, column=2, columnspan=1, sticky="NSWE", padx=2, pady=2
        )
        self.btn_browse.grid(row=1, column=3, sticky="NSE", padx=2, pady=2)

        # -- Format filters --------------------------------------------------
        self.FrFilters = Labelframe(
            self, name="filters", text=txt.get("gui_fr3", "Filters")
        )
        # formats options
        self.opt_shp = IntVar(self.FrFilters)  # able/disable shapefiles
        self.opt_tab = IntVar(self.FrFilters)  # able/disable MapInfo tables
        self.opt_kml = IntVar(self.FrFilters)  # able/disable KML
        self.opt_gml = IntVar(self.FrFilters)  # able/disable GML
        self.opt_geoj = IntVar(self.FrFilters)  # able/disable GeoJSON
        self.opt_gxt = IntVar(self.FrFilters)  # able/disable GXT
        self.opt_egdb = IntVar(self.FrFilters)  # able/disable Esri FileGDB
        self.opt_spadb = IntVar(self.FrFilters)  # able/disable Spatalite DB
        self.opt_rast = IntVar(self.FrFilters)  # able/disable rasters
        self.opt_cdao = IntVar(self.FrFilters)  # able/disable CAO/DAO files
        self.opt_qgs = IntVar(self.FrFilters)  # able/disable Geospatial QGS

        # format choosen: check buttons
        caz_shp = Checkbutton(self.FrFilters, text=".shp", variable=self.opt_shp)
        caz_tab = Checkbutton(self.FrFilters, text=".tab", variable=self.opt_tab)
        caz_kml = Checkbutton(self.FrFilters, text=".kml", variable=self.opt_kml)
        caz_gml = Checkbutton(self.FrFilters, text=".gml", variable=self.opt_gml)
        caz_geoj = Checkbutton(self.FrFilters, text=".geojson", variable=self.opt_geoj)
        caz_gxt = Checkbutton(self.FrFilters, text=".gxt", variable=self.opt_gxt)
        caz_egdb = Checkbutton(
            self.FrFilters, text="Esri FileGDB", variable=self.opt_egdb
        )
        caz_spadb = Checkbutton(
            self.FrFilters, text="Spatialite", variable=self.opt_spadb
        )
        caz_rast = Checkbutton(
            self.FrFilters,
            text="rasters ({})".format(", ".join(self.li_raster_formats)),
            variable=self.opt_rast,
        )
        caz_cdao = Checkbutton(self.FrFilters, text="CAO/DAO", variable=self.opt_cdao)
        # widgets placement
        caz_shp.grid(row=1, column=0, sticky="NSWE", padx=2, pady=2)
        caz_tab.grid(row=1, column=1, sticky="NSWE", padx=2, pady=2)
        caz_kml.grid(row=1, column=2, sticky="NSWE", padx=2, pady=2)
        caz_gml.grid(row=1, column=3, sticky="NSWE", padx=2, pady=2)
        caz_geoj.grid(row=1, column=4, sticky="NSWE", padx=2, pady=2)
        caz_gxt.grid(row=1, column=5, sticky="NSWE", padx=2, pady=2)
        caz_rast.grid(row=2, column=0, columnspan=2, sticky="NSWE", padx=2, pady=2)
        caz_egdb.grid(row=2, column=2, columnspan=2, sticky="NSWE", padx=2, pady=2)
        caz_cdao.grid(row=2, column=4, columnspan=1, sticky="NSWE", padx=2, pady=2)
        caz_spadb.grid(row=2, column=5, columnspan=2, sticky="NSWE", padx=2, pady=2)

        # frames placement
        self.FrPath.grid(row=3, column=1, padx=2, pady=2, sticky="NSWE")
        self.FrFilters.grid(row=4, column=1, padx=2, pady=2, sticky="NSWE")

    def get_target_path(self, def_rep) -> str:
        """Browse and insert the path of target folder."""
        foldername = askdirectory(
            parent=self.p,
            initialdir=def_rep,
            mustexist=True,
            title=_("Pick DicoGIS start folder"),
        )

        # check if a folder has been choosen
        if isinstance(foldername, (str, Path)) and len(str(foldername)):
            try:
                self.ent_target.delete(0, END)
                self.ent_target.insert(0, foldername)
            except Exception as err:
                logger.warning(err)
                showinfo(
                    title=self.txt.get("nofolder"), message=self.txt.get("nofolder")
                )
                return False
        else:
            showinfo(title=self.txt.get("nofolder"), message=self.txt.get("nofolder"))
            return False

        # set the default output file
        self.p.master.ent_outxl_filename.delete(0, END)
        self.p.master.ent_outxl_filename.insert(
            0,
            f"DicoGIS_{path.split(self.target_path.get())[1]}_{today}.xlsx",
        )

        # count geofiles in a separated thread
        proc = threading.Thread(target=self.p.master.ligeofiles, args=(foldername,))
        proc.daemon = True
        proc.start()

        # end of function
        return foldername


# #############################################################################
# ##### Stand alone program ########
# ##################################

if __name__ == "__main__":
    """To test"""

    #
    def browse():
        print("Launch files browser")
        logger.info("Launch files browser")

    #
    root = Tk()
    target_path = StringVar(root)
    frame = TabFiles(root, path_browser=browse, path_var=target_path)
    frame.pack()
    root.mainloop()
