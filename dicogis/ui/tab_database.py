#! python3  # noqa: E265


"""
    Name:         TabDatabase
    Purpose:      Tab containing database widgets in DicoGIS Notebook.

    Author:       Julien Moura (@geojulien)
"""

# ##############################################################################
# ########## Libraries #############
# ##################################


# Standard library
import logging
from tkinter import IntVar, StringVar, Tk
from tkinter.ttk import Checkbutton, Entry, Frame, Label, Labelframe

# ##############################################################################
# ############ Globals ############
# #################################

# LOG
logger = logging.getLogger(__name__)

# ##############################################################################
# ########## Classes ###############
# ##################################


class TabSGBD(Frame):
    """Tab form for server database connections.

    Args:
        Frame: inherited ttk.Frame
    """

    def __init__(self, parent, localized_strings: dict | None = None):
        """UI tab for databases initialization.

        Args:
            parent: tkinter parent object
            localized_strings: translated strings. Defaults to None.
        """
        self.parent = parent
        Frame.__init__(self)

        # handle empty localized strings
        if not localized_strings:
            localized_strings = {}

        # subframe
        self.FrDb = Labelframe(
            self, name="database", text=localized_strings.get("gui_fr2", "PostGIS")
        )

        # DB variables
        self.opt_pg_views = IntVar(self.FrDb)  # able/disable PostGIS views
        self.host = StringVar(self.FrDb, "localhost")
        self.port = IntVar(self.FrDb, 5432)
        self.db_name = StringVar(self.FrDb)
        self.user = StringVar(self.FrDb, "postgres")
        self.password = StringVar(self.FrDb)

        # Form widgets
        self.ent_host = Entry(self.FrDb, textvariable=self.host)
        self.ent_port = Entry(self.FrDb, textvariable=self.port, width=5)
        self.ent_db_name = Entry(self.FrDb, textvariable=self.db_name)
        self.ent_user = Entry(self.FrDb, textvariable=self.user)
        self.ent_password = Entry(self.FrDb, textvariable=self.password, show="*")

        caz_pg_views = Checkbutton(
            self.FrDb,
            text=localized_strings.get("gui_views", "Views enabled"),
            variable=self.opt_pg_views,
        )

        # Label widgets
        self.lb_host = Label(self.FrDb, text=localized_strings.get("gui_host", "Host:"))
        self.lb_port = Label(self.FrDb, text=localized_strings.get("gui_port", "Port:"))
        self.lb_db_name = Label(
            self.FrDb, text=localized_strings.get("gui_db", "Database:")
        )
        self.lb_user = Label(
            self.FrDb, text=localized_strings.get("gui_user", "Username:")
        )
        self.lb_password = Label(
            self.FrDb, text=localized_strings.get("gui_mdp", "Password:")
        )
        # widgets placement
        self.lb_host.grid(row=0, column=0, sticky="NSWE", padx=2, pady=2)
        self.ent_host.grid(row=0, column=1, sticky="NSWE", padx=2, pady=2)
        self.lb_port.grid(row=1, column=0, sticky="NSWE", padx=2, pady=2)
        self.ent_port.grid(row=1, column=1, sticky="NSWE", padx=2, pady=2)
        self.lb_db_name.grid(row=2, column=0, sticky="NSWE", padx=2, pady=2)
        self.ent_db_name.grid(row=2, column=1, sticky="NSWE", padx=2, pady=2)
        self.lb_user.grid(row=3, column=0, sticky="NSWE", padx=2, pady=2)
        self.ent_user.grid(row=3, column=1, sticky="NSWE", padx=2, pady=2)
        self.lb_password.grid(row=4, column=0, sticky="NSWE", padx=2, pady=2)
        self.ent_password.grid(row=4, column=1, sticky="NSWE", padx=2, pady=2)
        caz_pg_views.grid(row=5, column=0, sticky="NSWE", padx=2, pady=2)

        # frame position
        self.FrDb.grid(row=0, column=0, sticky="NSWE", padx=2, pady=2)


# #############################################################################
# ##### Stand alone program ########
# ##################################

if __name__ == "__main__":
    """To test"""
    root = Tk()
    frame = TabSGBD(root)
    frame.pack()
    root.mainloop()
