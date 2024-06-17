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
import threading
from datetime import date
from os import path
from pathlib import Path

# GUI
from tkinter import END, IntVar, StringVar, Tk
from tkinter.filedialog import askdirectory
from tkinter.messagebox import showinfo
from tkinter.ttk import Button, Checkbutton, Entry, Frame, Label, Labelframe
from typing import Optional

# project
from dicogis.constants import FormatsRaster
from dicogis.utils.check_path import check_path

# ##############################################################################
# ############ Globals ############
# #################################

logger = logging.getLogger(__name__)

# ##############################################################################
# ########## Classes ###############
# ##################################


class TabFiles(Frame):
    """Tab for listing and picking geodata files formats.

    Args:
        Frame: inherited ttk.Frame
    """

    def __init__(
        self,
        parent,
        listing_initial_folder: Path | None = None,
        localized_strings: dict | None = None,
    ):
        """Initializes UI tab for files browsing and filtering.

        Args:
            parent: tkinter parent object
            listing_initial_folder: initial folder fro ask directory dialog. Defaults
                to Path().home().
            localized_strings: translated strings. Defaults to None.
        """
        self.parent = parent
        Frame.__init__(self)

        # localized strings
        self.localized_strings = localized_strings
        if not self.localized_strings:
            self.localized_strings = {}

        # browse default path
        self.listing_initial_folder_path = listing_initial_folder
        if not self.listing_initial_folder_path:
            self.listing_initial_folder_path = Path().home()

        # -- VARIABLES -------------------------------------------------------
        self.target_path = StringVar()

        # -- Source path -----------------------------------------------------
        self.FrPath = Labelframe(
            self, name="files", text=self.localized_strings.get("gui_fr1", "Path")
        )

        # target folder
        self.lb_target = Label(
            self.FrPath, text=self.localized_strings.get("gui_path", "Folder path: ")
        )
        self.ent_target = Entry(
            master=self.FrPath, width=35, textvariable=self.target_path
        )
        self.btn_browse = Button(
            self.FrPath,
            text=self.localized_strings.get("gui_choix", "Browse"),
            command=lambda: self.on_browse_get_initial_listing_folder_path(),
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
            self, name="filters", text=self.localized_strings.get("gui_fr3", "Filters")
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
        self.opt_dxf = IntVar(self.FrFilters)  # able/disable DXF files

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
            text="rasters ({})".format(
                ", ".join([raster_format.value for raster_format in FormatsRaster])
            ),
            variable=self.opt_rast,
        )
        caz_dxf = Checkbutton(self.FrFilters, text="DXF", variable=self.opt_dxf)
        # widgets placement
        caz_shp.grid(row=1, column=0, sticky="NSWE", padx=2, pady=2)
        caz_tab.grid(row=1, column=1, sticky="NSWE", padx=2, pady=2)
        caz_kml.grid(row=1, column=2, sticky="NSWE", padx=2, pady=2)
        caz_gml.grid(row=1, column=3, sticky="NSWE", padx=2, pady=2)
        caz_geoj.grid(row=1, column=4, sticky="NSWE", padx=2, pady=2)
        caz_gxt.grid(row=1, column=5, sticky="NSWE", padx=2, pady=2)
        caz_rast.grid(row=2, column=0, columnspan=2, sticky="NSWE", padx=2, pady=2)
        caz_egdb.grid(row=2, column=2, columnspan=2, sticky="NSWE", padx=2, pady=2)
        caz_dxf.grid(row=2, column=4, columnspan=1, sticky="NSWE", padx=2, pady=2)
        caz_spadb.grid(row=2, column=5, columnspan=2, sticky="NSWE", padx=2, pady=2)

        # frames placement
        self.FrPath.grid(row=3, column=1, padx=2, pady=2, sticky="NSWE")
        self.FrFilters.grid(row=4, column=1, padx=2, pady=2, sticky="NSWE")

    def on_browse_get_initial_listing_folder_path(self) -> Optional[Path]:
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

        foldername = askdirectory(
            parent=self.parent,
            initialdir=self.listing_initial_folder_path,
            mustexist=True,
            title=self.localized_strings.get("nofolder", "Pick DicoGIS start folder"),
        )

        # check if a folder has been choosen
        if isinstance(foldername, (str, Path)) and len(str(foldername)):
            try:
                self.ent_target.delete(0, END)
                self.ent_target.insert(0, foldername)
            except Exception as err:
                logger.warning(err)
                showinfo(
                    title=self.localized_strings.get("nofolder", "No folder selected"),
                    message=self.localized_strings.get(
                        "nofolder", "A folder is required."
                    ),
                )
                return None
        else:
            showinfo(
                title=self.localized_strings.get("nofolder", "No folder selected"),
                message=self.localized_strings.get("nofolder", "A folder is required."),
            )
            return None

        # set the default output file
        self.parent.master.ent_outxl_filename.delete(0, END)
        self.parent.master.ent_outxl_filename.insert(
            0,
            f"DicoGIS_{path.split(self.target_path.get())[1]}_{date.today()}.xlsx",
        )

        # count geofiles in a separated thread
        proc = threading.Thread(
            target=self.parent.master.ligeofiles, args=(foldername,)
        )
        proc.daemon = True
        proc.start()

        # end of function
        return Path(foldername)


# #############################################################################
# ##### Stand alone program ########
# ##################################

if __name__ == "__main__":
    """To test"""
    root = Tk()
    target_path = StringVar(root)
    frame = TabFiles(root)
    frame.pack()
    root.mainloop()
