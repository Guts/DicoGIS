#! python3  # noqa: E265

"""
    Name:         MiscButtons
    Purpose:      Miscellaneous widgets for DicoGIS Notebook.

    Author:       Julien Moura (@geojulien)
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import gettext
import logging
from tkinter import PhotoImage, Tk, W
from tkinter.ttk import Button, Frame, Label
from webbrowser import open_new_tab

# package
from dicogis import __about__

# ##############################################################################
# ############ Globals ############
# #################################

_ = gettext.gettext
logger = logging.getLogger(__name__)

# ##############################################################################
# ########## Classes ###############
# ##################################


class MiscButtons(Frame):
    def __init__(self, parent, images_folder="../bin/imgs"):
        """Instanciating the output workbook."""
        self.parent = parent
        Frame.__init__(self)

        # logo
        self.icone = PhotoImage(
            master=self, file=images_folder / "DicoGIS_logo_200px.png"
        )
        Label(self, borderwidth=2, image=self.icone).grid(
            row=1, columnspan=2, column=0, padx=2, pady=2, sticky=W
        )
        # credits
        btn_credits = Button(
            self,
            text=parent.package_about.__copyright__,
            command=lambda: open_new_tab(parent.package_about.__uri__),
        )
        btn_credits.grid(row=2, columnspan=2, padx=2, pady=2, sticky="WE")

        # contact
        mailto = "mailto:{}?" "subject=[{}]%20Question".format(
            parent.package_about.__email__, parent.package_about.__title__
        )
        btn_contact = Button(
            self,
            text=_("Contact"),
            command=lambda: open_new_tab(mailto),
        )

        # source
        url_src = f"{parent.package_about.__uri__}issues"
        btn_src = Button(
            self,
            text=_("Report"),
            command=lambda: open_new_tab(url_src),
        )

        # documentation
        btn_doc = Button(
            self,
            text=_("Documentation"),
            command=lambda: open_new_tab(__about__.__uri_homepage__),
        )

        # griding
        btn_contact.grid(row=3, column=0, padx=2, pady=2, sticky="WE")
        btn_src.grid(row=3, column=1, padx=2, pady=2, sticky="EW")
        btn_doc.grid(row=4, column=0, columnspan=2, padx=2, pady=2, sticky="WE")


# #############################################################################
# ##### Stand alone program ########
# ##################################

if __name__ == "__main__":
    """To test"""
    root = Tk()
    frame = MiscButtons(root)
    frame.pack()
    root.mainloop()
