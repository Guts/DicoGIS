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
import logging
from tkinter import PhotoImage, Tk, W
from tkinter.ttk import Button, Frame, Label, Widget
from webbrowser import open_new_tab

# 3rd party
from typer import get_app_dir, launch

# package
from dicogis.__about__ import (
    __copyright__,
    __email__,
    __title__,
    __uri__,
    __uri_homepage__,
)
from dicogis.utils.texts import TextsManager
from dicogis.utils.utils import Utilities

# ##############################################################################
# ############ Globals ############
# #################################

app_dir = get_app_dir(app_name=__title__, force_posix=True)
logger = logging.getLogger(__name__)

# ##############################################################################
# ########## Classes ###############
# ##################################


class MiscButtons(Frame):
    """Miscellaneous buttons.

    Args:
        Frame: inherited ttk.Frame
    """

    def __init__(
        self,
        parent: Widget,
        localized_strings: dict | None = None,
        images_folder="bin/img",
    ):
        """UI frame on the application left side frame with logo and miscellaneous buttons.

        Args:
            parent: tkinter parent object
            localized_strings: translated strings. Defaults to None.
            init_widgets: option to create widgets during init or not. Defaults to True.
        """
        self.parent = parent
        super().__init__(parent)

        self.dicogis_utils = Utilities()
        self.dir_imgs = self.dicogis_utils.resolve_internal_path(
            internal_path=images_folder
        )

        # handle empty localized strings
        self.localized_strings = localized_strings
        if self.localized_strings is None:
            self.localized_strings = TextsManager().load_texts()

        # logo
        self.icone = PhotoImage(
            master=self, file=self.dir_imgs.joinpath("DicoGIS_logo_200px.png")
        )
        Label(self, borderwidth=2, image=self.icone).grid(
            row=1, columnspan=2, column=0, padx=2, pady=2, sticky=W
        )

        # credits
        btn_credits = Button(
            self,
            text=__copyright__,
            command=lambda: open_new_tab(__uri__),
        )
        btn_credits.grid(row=2, columnspan=2, padx=2, pady=2, sticky="WE")

        # contact
        mailto = f"mailto:{__email__}?subject=[{__title__}]%20Question"
        btn_contact = Button(
            self,
            text="Contact",
            command=lambda: open_new_tab(mailto),
        )

        # source
        url_src = f"{__uri__}issues"
        btn_src = Button(
            self,
            text="Report",
            command=lambda: open_new_tab(url_src),
        )

        # documentation
        btn_doc = Button(
            self,
            text=self.localized_strings.get(
                "ui_misc_btn_documentation", "Documentation"
            ),
            command=lambda: open_new_tab(__uri_homepage__),
        )

        # sponsor
        btn_support = Button(
            self,
            text=self.localized_strings.get("ui_misc_btn_support", "Fund & Support"),
            command=lambda: open_new_tab(f"{__uri_homepage__}misc/funding.html"),
        )

        # sponsor
        btn_app_dir = Button(
            self,
            text=self.localized_strings.get(
                "ui_misc_btn_app_dir", "Application folder"
            ),
            command=lambda: launch(app_dir),
        )

        # griding
        btn_contact.grid(row=3, column=0, padx=2, pady=2, sticky="WE")
        btn_src.grid(row=3, column=1, padx=2, pady=2, sticky="EW")
        btn_doc.grid(row=4, column=0, padx=2, pady=2, sticky="WE")
        btn_support.grid(row=4, column=1, padx=2, pady=2, sticky="WE")
        btn_app_dir.grid(row=5, columnspan=2, padx=2, pady=2, sticky="WE")


# #############################################################################
# ##### Stand alone program ########
# ##################################

if __name__ == "__main__":
    """To test"""
    root = Tk()
    frame = MiscButtons(root)
    frame.pack()
    root.mainloop()
