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
import logging
import subprocess
from os import R_OK, access, path
from pathlib import Path
from sys import exit
from sys import platform as opersys
from tkinter import ACTIVE, DISABLED
from tkinter.filedialog import asksaveasfilename  # dialogs
from tkinter.messagebox import showerror as avert
from typing import Optional

# Imports depending on operating system
if opersys == "win32":
    """windows"""
    from os import startfile  # to open a folder/file
else:
    pass

# package
from dicogis.export.md2xlsx import MetadataToXlsx

# ##############################################################################
# ############ Globals ############
# #################################

# LOG
logger = logging.getLogger(__name__)

# ############################################################################
# ######### Classes #############
# ###############################


class Utilities:
    def __init__(self):
        """DicoGIS specific utilities"""
        super().__init__()

    @classmethod
    def open_dir_file(self, target):
        """Open a file or directory in the explorer of the operating system."""
        # check if the file or the directory exists
        if not path.exists(target):
            raise OSError(f"No such file: {target}")

        # check the read permission
        if not access(target, R_OK):
            raise OSError(f"Cannot access file: {target}")

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

    @classmethod
    def safe_save(
        self,
        output_object: MetadataToXlsx,
        dest_dir: str = r".",
        dest_filename: str = "DicoGIS.xlsx",
        ftype: str = "Excel Workbook",
        dlg_title: Optional[str] = "DicoGIS - Save output Excel Workbook",
        gui: bool = True,
    ):
        """Safe save output file."""
        # Prompt of folder where save the file
        if gui:
            out_name = asksaveasfilename(
                initialdir=dest_dir,
                initialfile=dest_filename,
                defaultextension=".xlsx",
                filetypes=[(ftype, "*.xlsx")],
                title=dlg_title,
            )
        else:
            out_name = dest_filename

        if not isinstance(out_name, (str, Path)) and len(str(out_name)):
            logger.warning(f"No output file selected: {out_name}")
            return None

        # convert into Path object
        out_path = Path(dest_dir).joinpath(out_name)

        # check if the extension is correctly indicated
        if out_path.suffix != ".xlsx":
            out_path = out_path.with_suffix(".xlsx")

        # save
        if out_path.name != ".xlsx":
            try:
                output_object.save(filename=out_path)
            except OSError:
                if gui:
                    avert(
                        title="Concurrent access",
                        message="Please close Microsoft Excel before saving.",
                    )
                logger.error(
                    "Unable to save the file. Is the file already opened in a software?"
                )
                return out_name
            except Exception as err:
                logger.critical(
                    "Something happened during workbook saving operations. Trace: {}".format(
                        err
                    )
                )
        else:
            if gui:
                avert(title="Not saved", message="You cancelled saving operation")
                exit()

        # End of function
        return out_name, out_path

    @classmethod
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
    """standalone execution"""
    utils = Utilities()
