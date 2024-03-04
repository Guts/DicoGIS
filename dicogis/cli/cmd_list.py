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
from dicogis.__about__ import __title__, __version__
from dicogis.constants import SUPPORTED_FORMATS
from dicogis.export.md2xlsx import MetadataToXlsx
from dicogis.listing.geodata_listing import check_usable_pg_services, find_geodata_files
from dicogis.utils.environment import get_gdal_version, get_proj_version
from dicogis.utils.texts import TextsManager

# ############################################################################
# ########## Globals ###############
# ##################################

cli_list = typer.Typer(help="List (inventory) operations.")
state = {"verbose": False}
APP_NAME = f"{__title__}_list"
logger = logging.getLogger(__name__)
default_formats = ",".join([f.name for f in SUPPORTED_FORMATS])

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
            envvar="DICOGIS_START_FOLDER",
            file_okay=False,
            help="Starting folder for listing files. "
            "The folder must exist and be readable."
            "If None, files listing is ignored. Defaults to None.",
            readable=True,
            resolve_path=True,
        ),
    ] = None,
    formats: Annotated[
        str,
        typer.Option(
            envvar="DICOGIS_FORMATS_LIST",
            help="List of files extensions to include into listing. "
            "Must be part of supported formats. "
            "Defaults to every supported formats.",
        ),
    ] = default_formats,
    pg_services: Annotated[
        Optional[list[str]],
        typer.Option(
            envvar="DICOGIS_POSTGRES_SERVICES",
            help="name(s) of PostgreSQL services to use. It's a repeatable option. "
            "If None, database listing is ignored. Defaults to None.",
        ),
    ] = None,
    out_prettify_size: Annotated[
        bool,
        typer.Option(
            is_flag=True,
            help="Enable prettified files size in output. "
            "Example: 1 ko instead of 1024.",
        ),
    ] = False,
    verbose: bool = False,
):
    """Command to list geodata files starting from a folder and/or databases using \
        connection listed in pg_service.conf.

    Args:
        input_folder (Annotated[Optional[Path], typer.Option): starting folder for files.
            Defaults to None.
        formats (Annotated[ str, typer.Option, optional): list of format extensions to
            list. Defaults to every supported format.
        pg_services (Annotated[Optional[list[str]], typer.Option, optional): name(s) of
            PostgreSQL services to use. Repeatable. If None, database listing is
            ignored. Defaults to None.
        verbose (bool, optional): enable verbose mode. Defaults to False.
    """
    if verbose:
        state["verbose"] = True
        logger.setLevel = logging.DEBUG

    logger.debug(
        f"{APP_NAME} parameters: {input_folder=} - {formats=} - {pg_services=} - {verbose=}"
    )
    app_dir = typer.get_app_dir(APP_NAME)

    # log some context information
    logger.info(f"DicoGIS version: {__version__}")
    logger.debug(f"DicoGIS working folder: {app_dir}")
    logger.info(f"GDAL: {get_gdal_version()}")
    logger.info(f"PROJ: {get_proj_version()}")

    # check minimal parameters
    # note: pg_services defaults to [] not to None
    if input_folder is None and not pg_services:
        rich.print(
            "[bold red]Error: You must provide at least one of the options: "
            "input_folder or pg_services[/bold red]"
        )
        raise typer.Exit(code=1)

    # TODO: check if specified formats are supported

    # i18n
    dir_locale = Path(__file__).parent.parent.joinpath("locale")
    txt_manager = TextsManager(dir_locale)

    # look for geographic data files
    if input_folder is not None:
        geodata_find = find_geodata_files(start_folder=input_folder)
        rich.print(geodata_find)

        # creating the Excel workbook
        xl_workbook = MetadataToXlsx(
            texts=txt_manager,
            opt_size_prettify=out_prettify_size,
        )

    # look for geographic database
    if pg_services:
        print("Looking for geo SGBD")
        pg_services = check_usable_pg_services(requested_pg_services=pg_services)


# ############################################################################
# #### Stand alone program ########
# #################################
if __name__ == "__main__":
    """standalone execution"""
    cli_list()
