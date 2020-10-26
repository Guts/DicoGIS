#! python3  # noqa: E265


"""
    Name:         TabCredits
    Purpose:      Tab containing credits and licencse informations in DicoGIS Notebook.

    Author:       Julien Moura (@geojulien)
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import logging
from tkinter import ACTIVE, DISABLED, Tk
from tkinter.ttk import Frame, Label

# 3rd party
from dxfgrabber import VERSION as dxfgrabber_version
from openpyxl import __version__ as openpyxl_version
from osgeo import __version__ as gdal_version

# ##############################################################################
# ############ Globals ############
# #################################

# LOG
logger = logging.getLogger(__name__)

# ##############################################################################
# ########## Classes ###############
# ##################################


class TabCredits(Frame):
    def __init__(self, parent, txt=dict(), switcher=None):
        """Instanciating the output workbook."""
        self.parent = parent
        Frame.__init__(self)

        # subframes
        self.FrCreditsVersions = Frame(self, name="credits_versions")
        # positionning
        self.FrCreditsVersions.grid(row=0, column=0, sticky="WE", padx=2, pady=2)

        # -- Widgets definition --------------------------------------------------------
        # DXFGrabber
        self.cred_lb_dxfgrabber_name = Label(self.FrCreditsVersions, text="DXFGrabber")
        self.cred_lb_dxfgrabber_value = Label(
            self.FrCreditsVersions, text=dxfgrabber_version
        )

        # GDAL
        self.cred_lb_gdal_name = Label(self.FrCreditsVersions, text="GDAL")
        self.cred_lb_gdal_value = Label(self.FrCreditsVersions, text=gdal_version)

        # OpenPyXL
        self.cred_lb_openpyxl_name = Label(self.FrCreditsVersions, text="OpenPyXL")
        self.cred_lb_openpyxl_value = Label(
            self.FrCreditsVersions, text=openpyxl_version
        )

        # -- Widgets placement ---------------------------------------------------------
        self.cred_lb_dxfgrabber_name.grid(row=0, column=0, sticky="WE", padx=2, pady=2)
        self.cred_lb_dxfgrabber_value.grid(row=0, column=1, sticky="WE", padx=2, pady=2)
        self.cred_lb_gdal_name.grid(row=1, column=0, sticky="WE", padx=2, pady=2)
        self.cred_lb_gdal_value.grid(row=1, column=1, sticky="WE", padx=2, pady=2)
        self.cred_lb_openpyxl_name.grid(row=2, column=0, sticky="WE", padx=2, pady=2)
        self.cred_lb_openpyxl_value.grid(row=2, column=1, sticky="WE", padx=2, pady=2)


# #############################################################################
# ##### Stand alone program ########
# ##################################

if __name__ == "__main__":
    """To test"""
    #
    def ui_switch(cb_value, parent):
        """Change state of  all children widgets within a parent class.

        cb_value=boolean
        parent=Tkinter class with children (Frame, Labelframe, Tk, etc.)
        """
        if cb_value.get():
            for child in parent.winfo_children():
                child.configure(state=ACTIVE)
        else:
            for child in parent.winfo_children():
                child.configure(state=DISABLED)
        # end of function
        return

    # try it
    root = Tk()
    frame = TabCredits(root, switcher=ui_switch)
    frame.pack()
    root.mainloop()
