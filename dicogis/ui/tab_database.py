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
from tkinter import IntVar, StringVar, Tk, Toplevel
from tkinter.messagebox import showerror
from tkinter.ttk import (
    Button,
    Checkbutton,
    Combobox,
    Entry,
    Frame,
    Label,
    Labelframe,
    Widget,
)

# 3rd party
import pgserviceparser

# project
from dicogis.models.database_connection import DatabaseConnection
from dicogis.utils.texts import TextsManager

# ##############################################################################
# ############ Globals ############
# #################################

# LOG
logger = logging.getLogger(__name__)

# ##############################################################################
# ########## Classes ###############
# ##################################


class TabDatabaseServer(Frame):
    """Tab form for server database connections.

    Args:
        Frame: inherited ttk.Frame
    """

    def __init__(
        self,
        parent: Widget,
        localized_strings: dict | None = None,
        init_widgets: bool = True,
    ):
        """UI tab for databases initialization.

        Args:
            parent: tkinter parent object
            localized_strings: translated strings. Defaults to None.
            init_widgets: option to create widgets during init or not. Defaults to True.
        """
        super().__init__(parent)

        # attributes
        try:
            self.pg_services_names = pgserviceparser.service_names()
        except pgserviceparser.ServiceFileNotFound as err:
            logger.info(
                f"Unable to find the pg_service.conf file: {err} "
                "Using empty list for pg_services_names.",
            )
            self.pg_services_names = []

        # handle empty localized strings
        self.localized_strings = localized_strings
        if self.localized_strings is None:
            self.localized_strings = TextsManager().load_texts()

        if init_widgets:
            self.create_widgets()

    def create_widgets(self) -> None:
        """Create and layout the widgets for the frame."""

        # subframe
        self.FrameDatabaseServicePicker = Labelframe(
            self, name="database", text=self.localized_strings.get("gui_fr2", "PostGIS")
        )

        # DB variables
        self.opt_pg_views = IntVar(
            self.FrameDatabaseServicePicker
        )  # able/disable PostGIS views

        # Form widgets
        self.ddl_pg_services = Combobox(
            self.FrameDatabaseServicePicker,
            values=self.pg_services_names,
            state="readonly",
        )

        self.caz_pg_views = Checkbutton(
            self.FrameDatabaseServicePicker,
            text=self.localized_strings.get("gui_views", "Views enabled"),
            variable=self.opt_pg_views,
        )

        # Label widgets
        self.lb_pg_services = Label(
            self.FrameDatabaseServicePicker,
            text=self.localized_strings.get("gui_pg_service", "PG service:"),
        )

        # Button to open modal dialog
        self.open_form_button = Button(
            self.FrameDatabaseServicePicker,
            text=self.localized_strings.get("gui_database_form", "+"),
            command=self.open_form,
        )

        # widgets placement
        self.lb_pg_services.grid(row=0, column=0, sticky="NSWE", padx=2, pady=2)
        self.ddl_pg_services.grid(
            row=0, column=1, columnspan=2, sticky="NSWE", padx=2, pady=2
        )
        self.open_form_button.grid(row=0, column=3, padx=2, pady=2)
        self.caz_pg_views.grid(row=1, column=0, sticky="NSWE", padx=2, pady=2)

        # frame position
        self.FrameDatabaseServicePicker.grid(
            row=0, column=0, sticky="NSWE", padx=2, pady=2
        )

    def open_form(self) -> None:
        """Open the modal dialog for database form."""
        form = DatabaseNewConnectionForm(self)
        self.wait_window(form)

        # Retrieve the collected data after the form is closed
        if not isinstance(form.out_database_connection, DatabaseConnection):
            logger.debug("No database connection created.")
            return

        save_status, log_msg = form.out_database_connection.store_in_pgservice_file()
        if save_status:
            logger.info(log_msg)
            self.li_pg_services = self.ddl_pg_services["values"] = tuple(
                pgserviceparser.service_names()
            )
        else:
            logger.error(log_msg, stack_info=True)
            showerror(
                title=self.localized_strings.get(
                    "gui_database_save_new_service_error", "+"
                ),
                message=log_msg,
            )


class DatabaseNewConnectionForm(Toplevel):
    """Form to create a new database connection."""

    out_database_connection: DatabaseConnection | None = None

    def __init__(
        self,
        parent: Widget,
        localized_strings: dict | None = None,
        init_widgets: bool = True,
        is_modal: bool = True,
    ) -> None:
        """Initialize the DatabaseForm modal dialog.

        Args:
            parent (Widget): The parent widget.
            localized_strings: translated strings. Defaults to None.
            init_widgets: option to create widgets during init or not. Defaults to True.
            is_modal: option to make the dialog a modal. Defaults to True.

        """
        super().__init__(parent)

        # variables
        self.service_name = StringVar(self)
        self.database_name = StringVar(self)
        self.host = StringVar(self)
        self.port = IntVar(self)
        self.user = StringVar(self)
        self.password = StringVar(self)

        # handle empty localized strings
        self.localized_strings = localized_strings
        if self.localized_strings is None:
            self.localized_strings = TextsManager().load_texts()

        self.title(
            self.localized_strings.get(
                "gui_database_connection_form_title", "Add a new database connection"
            )
        )

        if init_widgets:
            self.create_widgets()

        if is_modal:
            # Make this window a modal dialog
            self.transient(parent)
            self.grab_set()
            self.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self) -> None:
        """Create and layout the widgets."""

        # labels
        self.lb_service_name = Label(
            self,
            text=self.localized_strings.get(
                "gui_database_service_name", "Service name:"
            ),
        )
        self.lb_host = Label(self, text=self.localized_strings.get("gui_host", "Host:"))
        self.lb_port = Label(self, text=self.localized_strings.get("gui_port", "Port:"))
        self.lb_db_name = Label(
            self, text=self.localized_strings.get("gui_db", "Database:")
        )
        self.lb_user = Label(
            self, text=self.localized_strings.get("gui_user", "Username:")
        )
        self.lb_password = Label(
            self, text=self.localized_strings.get("gui_mdp", "Password:")
        )

        self.ent_service_name = Entry(self, textvariable=self.service_name)
        self.ent_host = Entry(self, textvariable=self.host)
        self.ent_port = Entry(self, textvariable=self.port, width=5)
        self.ent_db_name = Entry(self, textvariable=self.database_name)
        self.ent_user = Entry(self, textvariable=self.user)
        self.ent_password = Entry(self, textvariable=self.password, show="*")

        # widgets placement
        self.lb_service_name.grid(row=0, column=0, sticky="NSWE", padx=2, pady=2)
        self.ent_service_name.grid(row=0, column=1, sticky="NSWE", padx=2, pady=2)
        self.lb_host.grid(row=1, column=0, sticky="NSWE", padx=2, pady=2)
        self.ent_host.grid(row=1, column=1, sticky="NSWE", padx=2, pady=2)
        self.lb_host.grid(row=1, column=0, sticky="NSWE", padx=2, pady=2)
        self.ent_host.grid(row=1, column=1, sticky="NSWE", padx=2, pady=2)
        self.lb_port.grid(row=2, column=0, sticky="NSWE", padx=2, pady=2)
        self.ent_port.grid(row=2, column=1, sticky="NSWE", padx=2, pady=2)
        self.lb_db_name.grid(row=3, column=0, sticky="NSWE", padx=2, pady=2)
        self.ent_db_name.grid(row=3, column=1, sticky="NSWE", padx=2, pady=2)
        self.lb_user.grid(row=4, column=0, sticky="NSWE", padx=2, pady=2)
        self.ent_user.grid(row=4, column=1, sticky="NSWE", padx=2, pady=2)
        self.lb_password.grid(row=5, column=0, sticky="NSWE", padx=2, pady=2)
        self.ent_password.grid(row=5, column=1, sticky="NSWE", padx=2, pady=2)

        # Submit button
        submit_button = Button(
            self,
            text=self.localized_strings.get("submit", "Submit"),
            command=self.submit,
        )
        submit_button.grid(row=6, column=0, columnspan=2, pady=10)
        cancel_button = Button(
            self,
            text=self.localized_strings.get("cancel", "Cancel"),
            command=self.on_close,
        )
        cancel_button.grid(row=6, column=2, pady=10)

    @property
    def get_form_as_database_connection(self) -> DatabaseConnection | None:
        """Return the collected data.

        Returns:
            dict: The collected data if available, None otherwise.
        """
        return self.out_database_connection

    def submit(self) -> None:
        """Collect data from the entries and process it."""
        # Collect the data from the entries and do something with it
        self.out_database_connection = DatabaseConnection(
            database_name=self.database_name.get(),
            service_name=self.service_name.get(),
            host=self.host.get(),
            port=self.port.get(),
            user_name=self.user.get(),
            user_password=self.password.get(),
        )

        # Close the form
        self.on_close()

    def on_close(self) -> None:
        """Handle the window close event."""
        self.grab_release()  # achieve modal loop
        self.destroy()


# #############################################################################
# ##### Stand alone program ########
# ##################################

if __name__ == "__main__":
    """To test"""
    logging.basicConfig(level=logging.DEBUG)

    root = Tk()
    frame = TabDatabaseServer(root)
    frame.pack()
    root.mainloop()
