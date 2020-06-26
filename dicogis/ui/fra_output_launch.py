#! python3  # noqa: E265


"""
    Name:         DicoGIS
    Purpose:      Automatize the creation of a dictionnary of geographic data \
                   contained in a folders structures. \
                   It produces an Excel output file (.xlsx)

    Author:       Julien Moura (@geojulien)
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# Standard library
from tkinter import W, PhotoImage
from tkinter.ttk import Style, Frame
from tkinter.ttk import Label, Button

import logging
from os import path
from webbrowser import open_new_tab

# ##############################################################################
# ############ Globals ############
# #################################

# LOG
logger = logging.getLogger(__name__)

# ##############################################################################
# ########## Classes ###############
# ##################################


class OutputLauncher(Frame):
    def __init__(self, parent, dicogis_path="../../"):
        """Instanciating the output workbook."""
        self.parent = parent
        Frame.__init__(self)

        # logo
        ico_path = path.join(path.abspath(dicogis_path), "data/img/DicoGIS_logo.gif")
        self.icone = PhotoImage(master=self, file=ico_path)
        Label(self, borderwidth=2, image=self.icone).grid(
            row=1, columnspan=2, column=0, padx=2, pady=2, sticky=W
        )
        # credits
        s = Style(self)
        s.configure("Kim.TButton", foreground="DodgerBlue", borderwidth=0)
        btn_credits = Button(
            self,
            text="by @GeoJulien\nGPL3 - 2017",
            style="Kim.TButton",
            command=lambda: open_new_tab("https://github.com/Guts/DicoGIS"),
        )
        btn_credits.grid(row=2, columnspan=2, padx=2, pady=2, sticky="WE")

        # contact
        mailto = (
            "mailto:DicoGIS%20Developer%20"
            "<julien.moura+dev@gmail.com>?"
            "subject=[DicoGIS]%20Question"
        )
        btn_contact = Button(
            self, text="\U00002709 " + "Contact", command=lambda: open_new_tab(mailto)
        )

        # source
        url_src = "https://github.com/Guts/DicoGIS/issues"
        btn_src = Button(
            self, text="\U000026A0 " + "Report", command=lambda: open_new_tab(url_src)
        )

        # griding
        btn_contact.grid(row=3, column=0, padx=2, pady=2, sticky="WE")
        btn_src.grid(row=3, column=1, padx=2, pady=2, sticky="EW")


# #############################################################################
# ##### Stand alone program ########
# ##################################

if __name__ == "__main__":
    """To test"""
    pass
