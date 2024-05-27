#! python3  # noqa: E265


"""
    Name:         TabSettings
    Purpose:      Tab containing settings widgets in DicoGIS Notebook.

    Author:       Julien Moura (@geojulien)
"""

# ##############################################################################
# ########## Libraries #############
# ##################################


# Standard library
import logging
from os import getenv
from tkinter import ACTIVE, DISABLED, BooleanVar, IntVar, StringVar, Tk
from tkinter.ttk import Checkbutton, Entry, Frame, Label, Labelframe
from typing import Callable

# ##############################################################################
# ############ Globals ############
# #################################

# LOG
logger = logging.getLogger(__name__)

# ##############################################################################
# ########## Classes ###############
# ##################################


class TabSettings(Frame):
    def __init__(self, parent, txt: dict, switcher: Callable = None):
        """Instanciating the output workbook."""
        self.parent = parent
        Frame.__init__(self)

        # subframes
        self.FrOptNetwork = Labelframe(
            self, name="lfr_settings_network", text=txt.get("Network", "Network")
        )

        self.FrOptExport = Labelframe(
            self,
            name="lfr_settings_export",
            text=txt.get("Export", "Export"),
        )

        # options values
        self.opt_proxy = IntVar(self)  # proxy option

        # Options form widgets
        caz_prox = Checkbutton(
            self.FrOptNetwork,
            text="Proxy",
            variable=self.opt_proxy,
            command=lambda: switcher(self.opt_proxy, self.FrOptProxy),
        )
        self.FrOptProxy = Labelframe(
            self.FrOptNetwork,
            name="lfr_settings_network_proxy",
            # text=txt.get("Proxy", "Proxy"),
            labelwidget=caz_prox,
        )

        # -- NETWORK OPTIONS -----------------------------------------------------------

        # proxy specific variables
        self.opt_ntlm = IntVar(self.FrOptProxy, 0)  # proxy NTLM protocol option
        self.prox_server = StringVar(self.FrOptProxy, "proxy.server.com")
        self.prox_port = IntVar(self.FrOptProxy, 80)
        self.prox_user = StringVar(self.FrOptProxy, "proxy_user")
        self.prox_pswd = StringVar(self.FrOptProxy, "****")

        # widgets
        self.prox_ent_H = Entry(self.FrOptProxy, textvariable=self.prox_server)
        self.prox_ent_P = Entry(self.FrOptProxy, textvariable=self.prox_port)
        self.prox_ent_M = Entry(self.FrOptProxy, textvariable=self.prox_pswd, show="*")

        self.prox_lb_H = Label(self.FrOptProxy, text=txt.get("gui_prox_server", "Host"))
        self.prox_lb_P = Label(self.FrOptProxy, text=txt.get("gui_port", "Port"))
        caz_ntlm = Checkbutton(self.FrOptProxy, text="NTLM", variable=self.opt_ntlm)
        self.prox_lb_M = Label(self.FrOptProxy, text=txt.get("gui_mdp", "Password"))

        # proxy widgets position
        self.prox_lb_H.grid(row=1, column=0, sticky="NSEW", padx=2, pady=2)
        self.prox_ent_H.grid(
            row=1, column=1, columnspan=2, sticky="NSEW", padx=2, pady=2
        )
        self.prox_lb_P.grid(row=1, column=2, sticky="NSEW", padx=2, pady=2)
        self.prox_ent_P.grid(
            row=1, column=3, columnspan=2, sticky="NSEW", padx=2, pady=2
        )
        caz_ntlm.grid(row=2, column=0, sticky="NSEW", padx=2, pady=2)
        self.prox_lb_M.grid(row=2, column=1, sticky="NSEW", padx=2, pady=2)
        self.prox_ent_M.grid(
            row=2, column=2, columnspan=2, sticky="NSEW", padx=2, pady=2
        )

        self.FrOptProxy.grid(
            row=0,
            column=0,
            sticky="NSWE",
            padx=2,
            pady=2,
        )
        self.FrOptNetwork.grid(
            row=0,
            column=0,
            sticky="NSWE",
            padx=2,
            pady=2,
        )

        # -- GENERAL OPTIONS -----------------------------------------------------------
        self.opt_export_size_prettify = BooleanVar(
            master=self, value=getenv("DICOGIS_EXPORT_SIZE_PRETTIFY", True)
        )
        caz_opt_export_size_prettify = Checkbutton(
            self.FrOptExport,
            text="Export: prettify files size",
            variable=self.opt_export_size_prettify,
        )
        caz_opt_export_size_prettify.grid(
            row=2, column=0, sticky="NSWE", padx=2, pady=2
        )

        self.opt_export_raw_path = BooleanVar(
            master=self, value=getenv("DICOGIS_EXPORT_RAW_PATH", False)
        )
        caz_opt_export_raw_path = Checkbutton(
            self.FrOptExport,
            text="Export: raw path",
            variable=self.opt_export_raw_path,
        )
        caz_opt_export_raw_path.grid(row=3, column=0, sticky="NSWE", padx=2, pady=2)

        self.opt_quick_fail = BooleanVar(
            master=self, value=getenv("DICOGIS_QUICK_FAIL", False)
        )
        caz_opt_quick_fail = Checkbutton(
            self.FrOptExport,
            text="Quick fail",
            variable=self.opt_quick_fail,
        )
        caz_opt_quick_fail.grid(row=3, column=0, sticky="NSWE", padx=2, pady=2)

        self.opt_end_process_notification_sound = BooleanVar(
            master=self, value=getenv("DICOGIS_ENABLE_NOTIFICATION_SOUND", True)
        )
        caz_opt_end_process_notification_sound = Checkbutton(
            self.FrOptExport,
            text="Play a notification sound when processing has finished.",
            variable=self.opt_end_process_notification_sound,
        )
        caz_opt_end_process_notification_sound.grid(
            row=4, column=0, sticky="NSWE", padx=2, pady=2
        )

        # positionning frames

        self.FrOptExport.grid(row=1, column=0, sticky="NSWE", padx=2, pady=2)


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
    frame = TabSettings(root, switcher=ui_switch)
    frame.pack()
    root.mainloop()
