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
from os import environ, getenv
from tkinter import ACTIVE, DISABLED, RAISED, BooleanVar, IntVar, StringVar
from tkinter.ttk import Button, Checkbutton, Entry, Frame, Label, Labelframe, Widget
from typing import Callable
from webbrowser import open_new_tab

# project
from dicogis.__about__ import __uri_homepage__
from dicogis.ui.collapsible_frame import ToggledFrame
from dicogis.ui.scrollable_table import ScrollableTable
from dicogis.utils.str2bool import str2bool
from dicogis.utils.texts import TextsManager

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
        parent: Widget,
        localized_strings: dict | None = None,
        init_widgets: bool = True,
        switcher: Callable = None,
    ):
        """Initializes UI tab for end-user options.

        Args:
            parent: tkinter parent object
            localized_strings: translated strings. Defaults to None.
            init_widgets: option to create widgets during init or not. Defaults to True.
        """
        super().__init__(parent)

        # handle empty localized strings
        self.localized_strings = localized_strings
        if self.localized_strings is None:
            self.localized_strings = TextsManager().load_texts()

        self.switcher = switcher

        if init_widgets:
            self.create_widgets()

    def create_widgets(self) -> None:
        """Create and layout the widgets for the frame."""
        # -- Subframes --
        # Proxy subframe with a check button
        self.opt_debug = BooleanVar(self, str2bool(getenv("DICOGIS_DEBUG", False)))
        self.opt_proxy = BooleanVar(self, False)

        self.caz_debug = Checkbutton(
            self,
            name="chb_debug_mode",
            text=self.localized_strings.get("option_debug", "Enable debug mode"),
            variable=self.opt_debug,
        )
        self.caz_debug.grid(sticky="W")

        caz_prox = Checkbutton(
            self,
            text="Proxy",
            variable=self.opt_proxy,
            command=lambda: self.switcher(self.opt_proxy, self.FrOptProxy),
        )
        self.FrOptProxy = Labelframe(
            self,
            name="lfr_settings_network_proxy",
            text=self.localized_strings.get("Proxy", "Proxy settings"),
            labelwidget=caz_prox,
        )

        self.FrOptExport = ToggledFrame(
            self,
            name="lfr_settings_export",
            in_text=self.localized_strings.get("Export", "Export"),
            start_opened=False,
            borderwidth=1,
            relief=RAISED,
        )

        self.FrOptEnv = ToggledFrame(
            self,
            name="lfr_settings_env_vars",
            in_text=self.localized_strings.get(
                "environment_variables", "Environment variables"
            ),
            start_opened=False,
            borderwidth=1,
            relief=RAISED,
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
            self.FrOptProxy, text=self.localized_strings.get("gui_prox_server", "Host:")
        )
        self.prox_lb_port = Label(
            self.FrOptProxy, text=self.localized_strings.get("gui_port", "Port:")
        )
        caz_ntlm = Checkbutton(self.FrOptProxy, text="NTLM", variable=self.opt_ntlm)
        self.prox_lb_user = Label(
            self.FrOptProxy, text=self.localized_strings.get("gui_user", "User name:")
        )

        self.prox_lb_password = Label(
            self.FrOptProxy,
            text=self.localized_strings.get("gui_mdp", "User password:"),
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
            self.FrOptExport.sub_frame,
            text=self.localized_strings.get(
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
            self.FrOptExport.sub_frame,
            text=self.localized_strings.get(
                "gui_options_export_raw_path", "Export: raw path"
            ),
            variable=self.opt_export_raw_path,
        )
        caz_opt_export_raw_path.grid(row=3, column=0, sticky="NSWE", padx=2, pady=2)

        self.opt_quick_fail = BooleanVar(
            master=self, value=getenv("DICOGIS_QUICK_FAIL", False)
        )
        caz_opt_quick_fail = Checkbutton(
            self.FrOptExport.sub_frame,
            text=self.localized_strings.get("gui_options_quick_fail", "Quick fail"),
            variable=self.opt_quick_fail,
        )
        caz_opt_quick_fail.grid(row=3, column=0, sticky="NSWE", padx=2, pady=2)

        self.opt_end_process_notification_sound = BooleanVar(
            master=self, value=getenv("DICOGIS_ENABLE_NOTIFICATION_SOUND", True)
        )
        caz_opt_end_process_notification_sound = Checkbutton(
            self.FrOptExport.sub_frame,
            text=self.localized_strings.get(
                "gui_options_notification_sound",
                "Play a notification sound when processing has finished.",
            ),
            variable=self.opt_end_process_notification_sound,
        )
        caz_opt_end_process_notification_sound.grid(
            row=4, column=0, sticky="NSWE", padx=2, pady=2
        )

        # -- Environment variables --
        btn_doc_env_vars = Button(
            self.FrOptEnv.sub_frame,
            text=self.localized_strings.get(
                "gui_options_supported_env_vars", "See supported variables"
            ),
            command=lambda: open_new_tab(
                f"{__uri_homepage__}usage/settings.html#using-environment-variables"
            ),
        )

        tab_env_vars = ScrollableTable(self.FrOptEnv.sub_frame)
        dicogis_env_vars = {
            env_var: value
            for env_var, value in environ.items()
            if env_var.startswith("DICOGIS_")
        }
        if nb_dicogis_envvars := len(dicogis_env_vars):
            logger.debug(
                f"{nb_dicogis_envvars} environment variables related to DicoGIS: "
            )
            for var_name, var_value in dicogis_env_vars.items():
                logger.debug(f"{var_name}={var_value}")
                tab_env_vars.tree.insert("", "end", values=(var_name, var_value))
        btn_doc_env_vars.grid(padx=2, pady=2, sticky="WE")
        tab_env_vars.grid(padx=2, pady=2, sticky="NSWE")

        # positionning frames
        self.FrOptProxy.grid(sticky="NSWE", padx=2, pady=2)
        self.FrOptExport.grid(sticky="NSWE", padx=2, pady=2)
        self.FrOptEnv.grid(sticky="NSWE", padx=2, pady=2)

        self.switcher(self.opt_proxy, self.FrOptProxy)


# #############################################################################
# ##### Stand alone program ########
# ##################################

if __name__ == "__main__":
    """To test"""
    from tkinter import Tk

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
