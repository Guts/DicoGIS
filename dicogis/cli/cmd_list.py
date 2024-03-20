#! python3  # noqa: E265

# ############################################################################
# ########## Libraries #############
# ##################################

# standard lib
import logging
from datetime import date
from locale import getlocale
from pathlib import Path
from typing import Annotated, Optional

# 3rd party
import typer
from rich import print

# project
from dicogis.__about__ import __title__, __version__
from dicogis.constants import SUPPORTED_FORMATS, AvailableLocales, OutputFormats
from dicogis.export.md2xlsx import MetadataToXlsx
from dicogis.georeaders.process_files import ProcessingFiles
from dicogis.georeaders.read_postgis import ReadPostGIS
from dicogis.listing.geodata_listing import check_usable_pg_services, find_geodata_files
from dicogis.utils.environment import get_gdal_version, get_proj_version
from dicogis.utils.notifier import send_system_notify
from dicogis.utils.texts import TextsManager
from dicogis.utils.utils import Utilities

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
    output_path: Annotated[
        Optional[Path],
        typer.Option(
            dir_okay=False,
            envvar="DICOGIS_OUTPUT_FILEPATH",
            file_okay=True,
            help="If not set, the file is created in the current working directory "
            "(cwd) and the filename is a concatenation of various informations.",
            resolve_path=True,
            writable=True,
        ),
    ] = None,
    output_format: Annotated[
        OutputFormats,
        typer.Option(
            case_sensitive=False,
            envvar="DICOGIS_OUTPUT_FORMAT",
            help="Output format. For now, only Excel (Microsoft Excel .xlsx) is "
            "supported. Here for the future!",
        ),
    ] = "excel",
    opt_notify_sound: Annotated[
        bool,
        typer.Option(
            envvar="DICOGIS_ENABLE_NOTIFICATION_SOUND",
            is_flag=True,
            help="Enable/disable notification's sound at the end of processing.",
        ),
    ] = True,
    opt_prettify_size: Annotated[
        bool,
        typer.Option(
            envvar="DICOGIS_EXPORT_SIZE_PRETTIFY",
            is_flag=True,
            help="Enable prettified files size in output. "
            "Example: 1 ko instead of 1024.",
        ),
    ] = False,
    language: Annotated[
        Optional[AvailableLocales],
        typer.Option(
            case_sensitive=False,
            envvar="DICOGIS_DEFAULT_LANGUAGE",
            help="Force language to use. If not set, the current default locale is used.",
        ),
    ] = None,
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
        f"{APP_NAME} parameters: {input_folder=} - {formats=} - {pg_services=} - "
        f"{verbose=} -{language=}"
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
        print(
            "[bold red]Error: You must provide at least one of the options: "
            "input_folder or pg_services[/bold red]"
        )
        raise typer.Exit(code=1)

    # TODO: check if specified formats are supported

    # i18n
    localized_strings: dict = {}
    if language is None:
        language = getlocale()[1]
    TextsManager().load_texts(dico_texts=localized_strings, language_code=language)

    # output format
    if output_format == "excel":
        # creating the Excel workbook
        xl_workbook = MetadataToXlsx(
            texts=localized_strings,
            opt_size_prettify=opt_prettify_size,
        )
    else:
        logger.error(
            NotImplementedError(
                f"Specified output format '{output_format}' is not available."
            )
        )
        typer.Exit(1)

    # look for geographic data files
    if input_folder is not None:
        li_vectors = []
        (
            num_folders,
            li_shapefiles,
            li_mapinfo_tab,
            li_kml,
            li_gml,
            li_geojson,
            li_gxt,
            li_raster,
            li_file_database_esri,
            li_dxf,
            li_dwg,
            li_dgn,
            li_cdao,
            li_file_databases,
            li_file_database_spatialite,
        ) = find_geodata_files(start_folder=input_folder)

        print(
            "Found: "
            f"{len(li_shapefiles)} shapefiles - "
            f"{len(li_mapinfo_tab)} tables (MapInfo) - "
            f"{len(li_kml)} KML - "
            f"{len(li_gml)} GML - "
            f"{len(li_geojson)} GeoJSON - "
            f"{len(li_gxt)} GXT"
            f"{len(li_raster)} rasters - "
            f"{len(li_file_databases)} file databases - "
            f"{len(li_cdao)} CAO/DAO - "
            f"in {num_folders}{localized_strings.get('log_numfold')}"
        )

        # grouping vectors lists
        li_vectors.extend(li_shapefiles)
        li_vectors.extend(li_mapinfo_tab)
        li_vectors.extend(li_kml)
        li_vectors.extend(li_gml)
        li_vectors.extend(li_geojson)
        li_vectors.extend(li_gxt)

        # check if there are some layers into the folder structure
        if not (
            len(li_vectors) + len(li_raster) + len(li_file_databases) + len(li_cdao)
        ):
            logger.error(localized_strings.get("nodata"))
            typer.Exit(1)

        # instanciate geofiles processor
        geofiles_processor = ProcessingFiles(
            output_workbook=xl_workbook,
            localized_strings=localized_strings,
            # list by tabs
            li_vectors=li_vectors,
            li_rasters=li_raster,
            li_file_databases=li_file_databases,
            li_cdao=li_cdao,
            # list by formats
            li_dxf=li_dxf,
            li_filegdb_esri=li_file_database_esri,
            li_filegdb_spatialite=li_file_database_spatialite,
            li_gml=li_gml,
            li_gxt=li_gxt,
            li_kml=li_kml,
            li_shapefiles=li_shapefiles,
            li_mapinfo_tab=li_mapinfo_tab,
            li_geojson=li_geojson,
            # options
            opt_analyze_cdao="dxf" in formats,
            opt_analyze_esri_filegdb="file_geodatabase_esri" in formats,
            opt_analyze_geojson="geojson" in formats,
            opt_analyze_gml="gml" in formats,
            opt_analyze_gxt="gxt" in formats,
            opt_analyze_kml="kml" in formats,
            opt_analyze_mapinfo_tab="geojson" in formats,
            opt_analyze_raster=any(
                [fmt in formats for fmt in ("ecw", "geotiff", "jpeg")]
            ),
            opt_analyze_shapefiles="esri_shapefile" in formats,
            opt_analyze_spatialite="file_geodatabase_spatialite" in formats,
        )

        # sheets and progress bar
        total_files = geofiles_processor.count_files_to_process()
        print(f"Start analyzing {total_files} files...")

        geofiles_processor.process_files_in_queue()

        # output file path
        if output_path is None:
            output_path = Path(f"DicoGIS_{input_folder.name}_{date.today()}.xlsx")

        xl_workbook.tunning_worksheets()
        saved = Utilities.safe_save(
            output_object=xl_workbook,
            dest_dir=f"{output_path.parent.resolve()}",
            dest_filename=f"{output_path.resolve()}",
            ftype="Excel Workbook",
            gui=False,
        )
        logger.info(f"Workbook saved: {saved[1]}")
        send_system_notify(
            notification_title="DicoGIS analysis ended",
            notification_message=f"DicoGIS successfully processed {total_files} files.",
            notification_sound=opt_notify_sound,
        )

    # look for geographic database
    if pg_services:
        print("Start looking for geographic table in PostGIS...")
        pg_services = check_usable_pg_services(requested_pg_services=pg_services)
        if not len(pg_services):
            logger.error("None of the specified pg_services is available.")
            raise typer.Exit(1)

        # configure output workbook
        xl_workbook.set_worksheets(has_sgbd=True)

        for pg_service in pg_services:
            dico_dataset = {}

            # testing connection settings
            sgbd_reader = ReadPostGIS(
                dico_dataset=dico_dataset, txt=localized_strings, service=pg_service
            )

            # check connection state
            if not sgbd_reader.conn:
                fail_reason = dico_dataset.get("conn_state")
                logger.error(
                    f"Connection failed using pg_service {pg_service}. Trace: {fail_reason}."
                )
                continue

            # show must go on
            logger.info(
                f"{sgbd_reader.conn.GetLayerCount()} tables found in PostGIS database."
            )

            # parsing the layers
            for idx_layer in range(sgbd_reader.conn.GetLayerCount()):
                layer = sgbd_reader.conn.GetLayerByIndex(idx_layer)
                # reset recipient data
                dico_dataset.clear()
                sgbd_reader.infos_dataset(layer)
                logger.info(f"Table examined: {layer.GetName()}")
                xl_workbook.store_md_sgdb(layer=dico_dataset)
                logger.debug("Layer metadata stored into workbook.")

        # output file path
        if output_path is None:
            output_path = Path(f"DicoGIS_PostGIS_{date.today()}.xlsx")

        xl_workbook.tunning_worksheets()
        saved = Utilities.safe_save(
            output_object=xl_workbook,
            dest_dir=f"{output_path.parent.resolve()}",
            dest_filename=f"{output_path.resolve()}",
            ftype="Excel Workbook",
            gui=False,
        )
        logger.info(f"Workbook saved: {saved[1]}")

        # output file path
        if output_path is None:
            output_path = f"DicoGIS_database_{date.today()}.xlsx"

        send_system_notify(
            notification_title="DicoGIS analysis ended",
            notification_message="DicoGIS successfully processed "
            f"{sgbd_reader.conn.GetLayerCount()} PostGIS tables. "
            "\nOpen the application to save the workbook.",
            notification_sound=opt_notify_sound,
        )


# ############################################################################
# #### Stand alone program ########
# #################################
if __name__ == "__main__":
    """standalone execution"""
    cli_list()
