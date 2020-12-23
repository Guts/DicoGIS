#! python3  # noqa: E265


"""
    Name:         Geodata Explorer
    Purpose:      Explore directory structure and list files and folders
                with geospatial data

    Author:       Julien Moura (@geojulien)
"""

# ############################################################################
# ######## Libraries #############
# ################################

# Standard library
from os import path, access, R_OK
from sys import exit, platform as opersys
import subprocess

from tkinter import ACTIVE, DISABLED
from tkinter.filedialog import asksaveasfilename  # dialogs
from tkinter.messagebox import showerror as avert

# Imports depending on operating system
if opersys == "win32":
    """ windows """
    from os import startfile  # to open a folder/file
else:
    pass

# ############################################################################
# ######### Classes #############
# ###############################


class Utilities(object):
    def __init__(self):
        """DicoGIS specific utilities"""
        super(Utilities, self).__init__()

    def open_dir_file(self, target):
        """Open a file or directory in the explorer of the operating system."""
        # check if the file or the directory exists
        if not path.exists(target):
            raise IOError("No such file: {0}".format(target))

        # check the read permission
        if not access(target, R_OK):
            raise IOError("Cannot access file: {0}".format(target))

        # open the directory or the file according to the os
        if opersys == "win32":  # Windows
            proc = startfile(path.realpath(target))

        elif opersys.startswith("linux"):  # Linux:
            proc = subprocess.Popen(
                ["xdg-open", target], stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

        elif opersys == "darwin":  # Mac:
            proc = subprocess.Popen(
                ["open", "--", target], stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

        else:
            raise NotImplementedError(
                "Your `%s` isn't a supported operating system`." % opersys
            )

        # end of function
        return proc

    def safe_save(
        self,
        wb,
        dest_dir=r".",
        dest_filename="DicoGIS.xlsx",
        ftype="Excel Workbook",
        dlg_title="DicoGIS - Save output Excel Workbook",
    ):
        """Safe save output file."""
        # Prompt of folder where save the file
        out_name = asksaveasfilename(
            initialdir=dest_dir,
            initialfile=dest_filename,
            defaultextension=".xlsx",
            filetypes=[(ftype, "*.xlsx")],
            title=dlg_title,
        )

        # check if the extension is correctly indicated
        if path.splitext(out_name)[1] != ".xlsx":
            out_name = out_name + ".xlsx"
        else:
            pass

        out_path = path.join(dest_dir, out_name)
        # save
        if out_name != ".xlsx":
            try:
                wb.save(out_path)
            except IOError:
                avert(
                    title="Concurrent access",
                    message="Please close Microsoft Excel before saving.",
                )
                return out_name
        else:
            avert(title="Not saved", message="You cancelled saving operation")
            exit()

        # End of function
        return out_name, out_path

    def ui_switch(self, cb_value, parent):
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


# ############################################################################
# #### Stand alone program ########
# #################################

if __name__ == "__main__":
    """ standalone execution """
    utils = Utilities()
