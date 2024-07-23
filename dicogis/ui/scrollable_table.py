from tkinter import Event
from tkinter.ttk import Frame, Scrollbar, Treeview, Widget

from dicogis.utils.texts import TextsManager


class ScrollableTable(Frame):
    """
    A scrollable table with two columns in read-only mode.

    Attributes:
        tree (ttk.Treeview): The Treeview widget for displaying the table.
        vsb (ttk.Scrollbar): The vertical scrollbar for the Treeview.
    """

    def __init__(
        self,
        parent: Widget,
        localized_strings: dict | None = None,
        init_widgets: bool = True,
    ):
        """Initialize the ScrollableTable frame.

        Args:
            parent (tk.Widget): The parent widget.
            init_widgets: option to create widgets during init or not. Defaults to True.
        """
        super().__init__(parent)

        # handle empty localized strings
        self.localized_strings = localized_strings
        if self.localized_strings is None:
            self.localized_strings = TextsManager().load_texts()

        if init_widgets:
            self.create_widgets()

    def create_widgets(self) -> None:
        """Create and layout the widgets for the frame."""
        # Create Treeview with 2 columns
        self.tree = Treeview(
            self,
            columns=("column1", "column2"),
            show="headings",
            height=3,
            selectmode="browse",
        )
        self.tree.heading("column1", text=self.localized_strings.get("key", "Key"))
        self.tree.heading("column2", text=self.localized_strings.get("value", "Value"))

        # Make the columns read-only
        # self.tree.bind("<1>", self.disable_event)

        # Add a vertical scrollbar
        self.vsb = Scrollbar(
            self,
            orient="vertical",
            name="env_var_table_vert_scroll",
            command=self.tree.yview,
        )
        self.tree.configure(yscrollcommand=self.vsb.set)

        # Layout the Treeview and Scrollbar
        self.tree.grid(row=0, column=0, sticky="NSEW")
        self.vsb.grid(row=0, column=1, sticky="NS")

        # Make the frame expandable
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def disable_event(self, event: Event) -> str:
        """
        Disable the event to make the Treeview read-only.

        Args:
            event (Event): The event object.

        Returns:
            str: "break" to indicate that the event should be ignored.
        """
        return "break"
