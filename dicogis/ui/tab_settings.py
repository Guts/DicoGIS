#! python3  # noqa: E265


"""
    Name:         TabSettings
    Purpose:      Tab containing settings widgets in DicoGIS Notebook.

    Author:       Julien Moura (@geojulien)
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

import logging

# Standard library
from tkinter import ACTIVE, DISABLED, IntVar, StringVar, Tk
from tkinter.ttk import Checkbutton, Entry, Frame, Label

# ##############################################################################
# ############ Globals ############
# #################################

# LOG
logger = logging.getLogger(__name__)

# ##############################################################################
# ########## Classes ###############
# ##################################


class TabSettings(Frame):
    def __init__(self, parent, txt=dict(), switcher=None):
        """Instanciating the output workbook."""
        self.parent = parent
        Frame.__init__(self)

        # subframes
        self.FrOptProxy = Frame(self, name="settings_proxy")

        # options values
        self.opt_proxy = IntVar(self)  # proxy option

        # Options form widgets
        caz_prox = Checkbutton(
            self,
            text="Proxy",
            variable=self.opt_proxy,
            command=lambda: switcher(self.opt_proxy, self.FrOptProxy),
        )

        # positionning
        caz_prox.grid(row=0, column=0, sticky="NSWE", padx=2, pady=2)
        self.FrOptProxy.grid(
            row=0, column=1, columnspan=8, sticky="NSWE", padx=2, pady=2, rowspan=3
        )

        # ------------------------------------------------------------------------
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
