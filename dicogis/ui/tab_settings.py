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
from typing import Callable, Optional

# ##############################################################################
# ############ Globals ############
# #################################

logger = logging.getLogger(__name__)

# ##############################################################################
# ########## Classes ###############
# ##################################


class TabSettings(Frame):
    """Tab form for end-user settings.

    Args:
        Frame: inherited ttk.Frame
    """

    def __init__(
        self,
        parent,
        localized_strings: Optional[dict] = None,
        switcher: Callable = None,
    ):
        """Initializes UI tab for end-user options.

        Args:
            parent: tkinter parent object
            localized_strings: translated strings. Defaults to None.
        """
        self.parent = parent
        Frame.__init__(self)

        # handle empty localized strings
        if not localized_strings:
            localized_strings = {}

        # -- Subframes --
        # Proxy subframe with a check button
        self.opt_proxy = BooleanVar(self, False)  # proxy optio
        caz_prox = Checkbutton(
            self,
            text="Proxy",
            variable=self.opt_proxy,
            command=lambda: switcher(self.opt_proxy, self.FrOptProxy),
        )
        self.FrOptProxy = Labelframe(
            self,
            name="lfr_settings_network_proxy",
            text=localized_strings.get("Proxy", "Proxy settings"),
            labelwidget=caz_prox,
        )

        self.FrOptExport = Labelframe(
            self,
            name="lfr_settings_export",
            text=localized_strings.get("Export", "Export"),
        )

        # -- NETWORK OPTIONS -----------------------------------------------------------

        # proxy specific variables
        self.opt_ntlm = IntVar(self.FrOptProxy, 0)  # proxy NTLM protocol option
        self.prox_server = StringVar(self.FrOptProxy, "proxy.server.com")
        self.prox_port = IntVar(self.FrOptProxy, 80)
        self.prox_user = StringVar(self.FrOptProxy, "proxy_user")
        self.prox_pswd = StringVar(self.FrOptProxy, "****")

        # widgets
        self.prox_ent_host = Entry(self.FrOptProxy, textvariable=self.prox_server)
        self.prox_ent_port = Entry(self.FrOptProxy, textvariable=self.prox_port)
        self.prox_ent_user = Entry(self.FrOptProxy, textvariable=self.prox_user)
        self.prox_ent_password = Entry(
            self.FrOptProxy, textvariable=self.prox_pswd, show="*"
        )

        self.prox_lb_host = Label(
            self.FrOptProxy, text=localized_strings.get("gui_prox_server", "Host:")
        )
        self.prox_lb_port = Label(
            self.FrOptProxy, text=localized_strings.get("gui_port", "Port:")
        )
        caz_ntlm = Checkbutton(self.FrOptProxy, text="NTLM", variable=self.opt_ntlm)
        self.prox_lb_user = Label(
            self.FrOptProxy, text=localized_strings.get("gui_user", "User name:")
        )

        self.prox_lb_password = Label(
            self.FrOptProxy, text=localized_strings.get("gui_mdp", "User password:")
        )

        # proxy widgets position
        self.prox_lb_host.grid(row=1, column=0, sticky="NSW", padx=2, pady=2)
        self.prox_ent_host.grid(row=1, column=1, sticky="NSE", padx=2, pady=2)
        self.prox_lb_port.grid(row=2, column=0, sticky="NSEW", padx=2, pady=2)
        self.prox_ent_port.grid(row=2, column=1, sticky="NSEW", padx=2, pady=2)
        self.prox_lb_user.grid(row=3, column=0, sticky="NSEW", padx=2, pady=2)
        self.prox_ent_user.grid(row=3, column=1, sticky="NSEW", padx=2, pady=2)
        self.prox_lb_password.grid(row=4, column=0, sticky="NSEW", padx=2, pady=2)
        self.prox_ent_password.grid(row=4, column=1, sticky="NSEW", padx=2, pady=2)
        caz_ntlm.grid(row=3, column=0, sticky="NSEW", padx=2, pady=2)

        # -- GENERAL OPTIONS -----------------------------------------------------------
        self.opt_export_size_prettify = BooleanVar(
            master=self, value=getenv("DICOGIS_EXPORT_SIZE_PRETTIFY", True)
        )
        caz_opt_export_size_prettify = Checkbutton(
            self.FrOptExport,
            text=localized_strings.get(
                "gui_options_export_size_prettify", "Export: prettify files size"
            ),
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
            text=localized_strings.get(
                "gui_options_export_raw_path", "Export: raw path"
            ),
            variable=self.opt_export_raw_path,
        )
        caz_opt_export_raw_path.grid(row=3, column=0, sticky="NSWE", padx=2, pady=2)

        self.opt_quick_fail = BooleanVar(
            master=self, value=getenv("DICOGIS_QUICK_FAIL", False)
        )
        caz_opt_quick_fail = Checkbutton(
            self.FrOptExport,
            text=localized_strings.get("gui_options_quick_fail", "Quick fail"),
            variable=self.opt_quick_fail,
        )
        caz_opt_quick_fail.grid(row=3, column=0, sticky="NSWE", padx=2, pady=2)

        self.opt_end_process_notification_sound = BooleanVar(
            master=self, value=getenv("DICOGIS_ENABLE_NOTIFICATION_SOUND", True)
        )
        caz_opt_end_process_notification_sound = Checkbutton(
            self.FrOptExport,
            text=localized_strings.get(
                "gui_options_notification_sound",
                "Play a notification sound when processing has finished.",
            ),
            variable=self.opt_end_process_notification_sound,
        )
        caz_opt_end_process_notification_sound.grid(
            row=4, column=0, sticky="NSWE", padx=2, pady=2
        )

        # positionning frames
        self.FrOptProxy.grid(sticky="NSWE", padx=2, pady=2)
        self.FrOptExport.grid(sticky="NSWE", padx=2, pady=2)

        switcher(self.opt_proxy, self.FrOptProxy)


# #############################################################################
# ##### Stand alone program ########
# ##################################

if __name__ == "__main__":
    """To test"""

    # faking switch method
    def ui_switch(cb_value: bool, parent):
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

    # try it
    root = Tk()
    frame = TabSettings(root, switcher=ui_switch)
    frame.pack()
    root.mainloop()
