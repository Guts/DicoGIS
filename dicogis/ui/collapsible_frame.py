#! python3  # noqa: E265


"""
    Name:         Custom collapsible frame
    Purpose:      Allow toggle a frame in pure Python Tkinter.

    Author:       Julien Moura (@geojulien)
    Sources:
        - ttkwidgets (GPL 3)
        - Onlyjus (https://stackoverflow.com/a/13169685/2556577)

"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import logging
from tkinter import BooleanVar
from tkinter.ttk import Button, Frame, Label, Widget

# ##############################################################################
# ############ Globals ############
# #################################

logger = logging.getLogger(__name__)


# ##############################################################################
# ########## Classes ###############
# ##################################


class ToggledFrame(Frame):
    """A frame that can be toggled to open and close."""

    def __init__(
        self,
        parent: Widget = None,
        in_text: str = "",
        toggle_width: int = 2,
        start_opened: bool = True,
        **kwargs,
    ):
        """Initializes UI tab for end-user options.

        Args:
            parent: tkinter parent object
            in_text: text to display next to the toggle arrow. Defaults to empty string.
            toggle_width: width of the tgogle button(in characters). Defaults to 2.
            kwargs: keyword arguments passed on to the :class:`ttk.Frame` initializer
        """
        super().__init__(parent, **kwargs)

        # variables
        self.is_open_var = BooleanVar(value=start_opened)

        # frame containing tool button and label
        self.title_frame = Frame(self)
        self.lbl_frame = Label(self.title_frame, text=in_text)
        self.btn_toggle = Button(
            self.title_frame,
            command=self.toggle,
            style="Toolbutton",
            text="-" if start_opened is True else "+",
            width=toggle_width,
        )

        self.sub_frame = Frame(self)

        self._grid_widgets()
        self.toggle()

    def _grid_widgets(self):
        """Grid frame widgets."""
        self.title_frame.grid(sticky="WE")
        self.title_frame.grid_columnconfigure(0, weight=1)
        self.lbl_frame.grid(row=0, column=0, sticky="W", padx=15)
        self.btn_toggle.grid(row=0, column=1, sticky="E")

    def toggle(self):
        """Toggle opened or closed."""
        if self.is_open_var.get():
            self._open = False
            self.sub_frame.grid(row=1, sticky="nswe")
            self.btn_toggle.configure(text="-")
        else:
            self._open = True
            self.sub_frame.grid_forget()

            self.btn_toggle.configure(text="+")

        self.is_open_var.set(not self.is_open_var.get())


if __name__ == "__main__":
    from tkinter import Tk
    from tkinter.ttk import Button

    root = Tk()

    collapsible_frame = ToggledFrame(
        parent=root,
        in_text="Rotate",
        start_opened=True,
        borderwidth=2,
        relief="raised",
    )
    collapsible_frame.pack()
    button = Button(
        collapsible_frame.sub_frame, text="Close window", command=root.destroy
    )
    button.grid()
    collapsible_frame.toggle()
    root.mainloop()
