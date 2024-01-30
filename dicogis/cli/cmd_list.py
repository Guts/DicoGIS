#! python3  # noqa: E265

# ############################################################################
# ########## Libraries #############
# ##################################

# standard lib
import logging
from pathlib import Path
from typing import Annotated, Optional

# 3rd party
import rich
import typer

# project
from dicogis.__about__ import __title__
from dicogis.listing.geodata_listing import find_geodata_files

# ############################################################################
# ########## Globals ###############
# ##################################

cli_list = typer.Typer(help="List (inventory) operations.")
state = {"verbose": False}
APP_NAME = f"{__title__}_list"
logger = logging.getLogger(__name__)


# ############################################################################
# ########## Functions #############
# ##################################


@cli_list.command(
    help="List geodata and extract metadata into an Excel (.xlsx) spreadsheet file."
)
def inventory(
    input_folder: Annotated[
        Optional[Path],
        typer.Option(
            dir_okay=True,
            file_okay=False,
            readable=True,
            resolve_path=True,
            envvar="DICOGIS_START_FOLDER",
        ),
    ],
    formats: Annotated[
        str,
        typer.Option(
            envvar="DICOGIS_FORMATS_LIST",
        ),
    ] = "shp,geotiff,geojson,kml",
):
    """Command to list geodata starting from a

    Args:
        input_folder (Annotated[Optional[Path], typer.Option): _description_
    """
    typer.echo(
        f"Analysing geodata stored in {input_folder}. Targetted formats: {formats}"
    )
    app_dir = typer.get_app_dir(APP_NAME)
    logger.warning(f"DicoGIS folder: {app_dir}")

    # TODO: check if specified formats are supported

    # look for geographic data
    geodata_find = find_geodata_files(start_folder=input_folder)
    rich.print(geodata_find)


# ############################################################################
# #### Stand alone program ########
# #################################
if __name__ == "__main__":
    """standalone execution"""
    cli_list()
