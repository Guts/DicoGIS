import tkinter as tk
from tkinter import ttk

import pgserviceparser


class DatabaseTab(tk.Frame):
    def __init__(self, parent: tk.Widget) -> None:
        """
        Initialize the DatabaseTab frame.

        Args:
            parent (tk.Widget): The parent widget.
        """
        super().__init__(parent)

        self.services_names = pgserviceparser.service_names()

        self.create_widgets()

    def create_widgets(self) -> None:
        """
        Create and layout the widgets for the DatabaseTab frame.
        """
        # Dropdown list
        self.service_var = tk.StringVar()
        self.service_dropdown = ttk.Combobox(self, textvariable=self.service_var)
        self.service_dropdown["values"] = self.services_names
        self.service_dropdown.grid(row=0, column=0, padx=10, pady=10)

        # Button to open modal dialog
        self.open_form_button = tk.Button(
            self, text="Open Form", command=self.open_form
        )
        self.open_form_button.grid(row=0, column=1, padx=10, pady=10)

    def open_form(self) -> None:
        """
        Open the modal dialog for database form.
        """
        form = DatabaseForm(self)
        self.wait_window(form)


class DatabaseForm(tk.Toplevel):
    def __init__(self, parent: tk.Widget) -> None:
        """
        Initialize the DatabaseForm modal dialog.

        Args:
            parent (tk.Widget): The parent widget.
        """
        super().__init__(parent)

        self.title("Database Form")

        # Make this window a modal dialog
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Fields
        self.fields = ["Host", "Port", "Database", "User", "Password"]
        self.entries: dict[str, tk.Entry] = {}

        for idx, field in enumerate(self.fields):
            label = tk.Label(self, text=field)
            label.grid(row=idx, column=0, padx=10, pady=5)

            entry = tk.Entry(self, show="*" if field == "Password" else None)
            entry.grid(row=idx, column=1, padx=10, pady=5)
            self.entries[field] = entry

        # Submit button
        submit_button = tk.Button(self, text="Submit", command=self.submit)
        submit_button.grid(row=len(self.fields), column=0, columnspan=2, pady=10)

    def submit(self) -> None:
        """
        Collect data from the entries and process it.
        """
        # Collect the data from the entries and do something with it
        data = {field: entry.get() for field, entry in self.entries.items()}
        print("Collected data:", data)  # Replace with actual processing logic

        # Close the form
        self.on_close()

    def on_close(self) -> None:
        """
        Handle the window close event.
        """
        self.grab_release()
        self.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    root.title("DicoGIS")
    DatabaseTab(root).pack(expand=True, fill="both")
    root.mainloop()
