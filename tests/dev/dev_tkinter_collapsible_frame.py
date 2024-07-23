import tkinter as tk
from tkinter import ttk


class CollapsibleFrame(ttk.Frame):
    """
    A collapsible frame that can be toggled to show or hide its content.
    """

    def __init__(self, parent: tk.Widget, title: str = "Collapsible Frame") -> None:
        """
        Initialize the CollapsibleFrame.

        Args:
            parent (tk.Widget): The parent widget.
            title (str): The title of the collapsible frame.
        """
        super().__init__(parent)

        # Variables
        self.is_collapsed = tk.BooleanVar(value=False)

        # Create a header frame to hold the toggle button and title
        self.header_frame = ttk.Frame(self)
        self.header_frame.grid(row=0, column=0, sticky="ew")
        self.header_frame.grid_columnconfigure(1, weight=1)

        # Toggle button
        self.toggle_button = ttk.Button(
            self.header_frame, text="▶", width=2, command=self.toggle_frame
        )
        self.toggle_button.grid(row=0, column=0, sticky="w")

        # Title label
        self.title_label = ttk.Label(self.header_frame, text=title, anchor="w")
        self.title_label.grid(row=0, column=1, sticky="w")

        # Frame to hold the content
        self.content_frame = ttk.Frame(self)

        # Add some sample content
        sample_label = ttk.Label(
            self.content_frame, text="This is a collapsible frame."
        )
        sample_label.grid(row=0, column=0, padx=10, pady=10)

        # Initially collapse the frame
        self.toggle_frame()

    def toggle_frame(self) -> None:
        """
        Toggle the visibility of the content frame.
        """
        if self.is_collapsed.get():
            self.content_frame.grid_forget()
            self.toggle_button.config(text="▶")
        else:
            self.content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
            self.toggle_button.config(text="▼")
        self.is_collapsed.set(not self.is_collapsed.get())


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Collapsible Frame Example")

    collapsible_frame = CollapsibleFrame(root, title="Toggle Frame")
    collapsible_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    root.mainloop()
