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
from dicogis.__about__ import __package_name__, __title__
from dicogis.constants import SUPPORTED_FORMATS, AvailableLocales, OutputFormats
from dicogis.export.base_serializer import MetadatasetSerializerBase
from dicogis.georeaders.process_files import ProcessingFiles
from dicogis.georeaders.read_postgis import ReadPostGIS
from dicogis.listing.geodata_listing import check_usable_pg_services, find_geodata_files
from dicogis.utils.journalizer import LogManager
from dicogis.utils.notifier import send_system_notify
from dicogis.utils.slugger import sluggy
from dicogis.utils.texts import TextsManager

# ############################################################################
# ########## Globals ###############
# ##################################

state = {"verbose": False}
logger = logging.getLogger(__name__)
default_formats = ",".join([f.name for f in SUPPORTED_FORMATS])
# ############################################################################
# ########## Functions #############
# ##################################


def determine_output_path(
    output_path: Path | str | None,
    output_format: str = "excel",
    input_folder: Path | None = None,
    pg_services: list[str] | None = None,
) -> Path:
    """Get the output path depending on options passed.

    Args:
        output_path: output path passed to inventory CLI
        output_format: input output format passed to inventory CLI
        input_folder: input folder passed to inventory CLI
        pg_services: list of ppostgres services names to use

    Raises:
        ValueError: if output format is not supported

    Returns:
        output path to use. A folder if output_format=='json',
            a file if output_format=='excel'
    """
    final_output_path = None
    if isinstance(pg_services, list):
        pg_srv_names = "__".join(
            sluggy(pg_service_name) for pg_service_name in pg_services
        )

    # output file path
    if output_path is None:
        if output_format == "excel":
            if isinstance(input_folder, Path):
                final_output_path = Path(
                    f"DicoGIS_{input_folder.name}_{date.today()}.xlsx"
                )
            elif isinstance(pg_services, list):
                final_output_path = Path(
                    f"DicoGIS_PostGIS_{pg_srv_names}_{date.today()}.xlsx"
                )
        elif output_format in ("json", "udata"):
            if isinstance(input_folder, Path):
                final_output_path = Path(f"DicoGIS_{input_folder.name}_{date.today()}")
            elif isinstance(pg_services, list):
                final_output_path = Path(f"DicoGIS_{pg_srv_names}_{date.today()}")
        else:
            raise ValueError(f"Unsupported output format: {output_format}.")
    else:
        final_output_path = output_path

    return final_output_path


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
            dir_okay=True,
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
    opt_open_output: Annotated[
        bool,
        typer.Option(
            envvar="DICOGIS_OPEN_OUTPUT",
            is_flag=True,
            help="Enable/disable auto opening output file when processing has finished.",
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
    opt_quick_fail: Annotated[
        bool,
        typer.Option(
            envvar="DICOGIS_QUICK_FAIL",
            is_flag=True,
            help="Enable quick fail instead of passing errors. Useful for debug.",
        ),
    ] = False,
    opt_raw_path: Annotated[
        bool,
        typer.Option(
            envvar="DICOGIS_EXPORT_RAW_PATH",
            is_flag=True,
            help="Enable raw path instead of hyperlink in formats which support it.",
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
    """List, extract metadata from geospatial datasets (files or database) and store it
    as files.

    Make an inventory of geodata files starting from a folder and/or
    databases using connection listed in pg_service.conf and store everything in an
    output file.

    Args:
        input_folder: starting folder for files. Defaults to None.
        formats: List of files extensions to include into listing. Defaults to every
            supported formats.
        pg_services: name(s) of PostgreSQL services to use. Repeatable. If None,
            database listing is ignored. Defaults to None.
        pg_services: name(s) of PostgreSQL services to use. Repeatable. If None,
            database listing is ignored. Defaults to None.
        language: language code to use. If not set, the current default locale is used.
            Defaults to None.
        verbose: enable verbose mode. Defaults to False.
    """
    app_dir = typer.get_app_dir(app_name=__title__, force_posix=True)
    # start logging
    if verbose:
        state["verbose"] = True

    logmngr = LogManager(
        console_level=logging.DEBUG if verbose else logging.WARNING,
        file_level=logging.DEBUG if verbose else logging.INFO,
        label=f"{__package_name__}-cli-inventory",
        folder=Path(app_dir).joinpath("logs"),
    )
    # add headers
    logmngr.headers()
    logger.debug(f"DicoGIS working folder: {app_dir}")
    logger.debug(
        f"CLI passed parameters: {input_folder=} - {formats=} - {pg_services=} - "
        f"{verbose=} -{language=}"
    )

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
    if language is None:
        language = getlocale()
    localized_strings = TextsManager().load_texts(language_code=language)

    # output format

    # look for geographic data files
    if input_folder is not None:
        output_path = determine_output_path(
            output_path=output_path,
            output_format=output_format,
            input_folder=input_folder,
        )

        output_serializer = MetadatasetSerializerBase.get_serializer_from_parameters(
            format_or_serializer=output_format,
            output_path=output_path,
            opt_prettify_size=opt_prettify_size,
            opt_raw_path=opt_raw_path,
        )

        li_vectors = []
        (
            num_folders,
            li_shapefiles,
            li_mapinfo_tab,
            li_kml,
            li_gml,
            li_geojson,
            li_geotiff,
            li_gxt,
            li_raster,
            li_file_database_esri,
            li_dxf,
            li_dwg,
            li_dgn,
            li_cdao,
            li_file_databases,
            li_file_database_spatialite,
            li_file_database_geopackage,
        ) = find_geodata_files(start_folder=input_folder)

        print(
            "Found: "
            f"{len(li_shapefiles)} shapefiles - "
            f"{len(li_mapinfo_tab)} tables (MapInfo) - "
            f"{len(li_kml)} KML - "
            f"{len(li_gml)} GML - "
            f"{len(li_geojson)} GeoJSON - "
            f"{len(li_gxt)} GXT - "
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
        li_raster.extend(li_geotiff)

        # check if there are some layers into the folder structure
        if not (
            len(li_vectors) + len(li_raster) + len(li_file_databases) + len(li_cdao)
        ):
            logger.error(localized_strings.get("nodata"))
            typer.Exit(1)

        # instanciate geofiles processor
        geofiles_processor = ProcessingFiles(
            serializer=output_serializer,
            localized_strings=localized_strings,
            # list by tabs
            li_vectors=li_vectors,
            li_rasters=li_raster,
            li_file_databases=li_file_databases,
            li_cdao=li_cdao,
            # list by formats
            li_dxf=li_dxf,
            li_flat_geodatabase_esri_filegdb=li_file_database_esri,
            li_flat_geodatabase_spatialite=li_file_database_spatialite,
            li_flat_geodatabase_geopackage=li_file_database_geopackage,
            li_geojson=li_geojson,
            li_geotiff=li_geotiff,
            li_gml=li_gml,
            li_gxt=li_gxt,
            li_kml=li_kml,
            li_mapinfo_tab=li_mapinfo_tab,
            li_shapefiles=li_shapefiles,
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
            # misc
            opt_quick_fail=opt_quick_fail,
        )

        # sheets and progress bar
        total_files = geofiles_processor.count_files_to_process()
        print(f"Start analyzing {total_files} files...")

        geofiles_processor.process_datasets_in_queue()

        send_system_notify(
            notification_title="DicoGIS analysis ended",
            notification_message=f"DicoGIS successfully processed {total_files} files.",
            notification_sound=opt_notify_sound,
        )
        if opt_open_output:
            typer.launch(url=f"{output_path.resolve()}")

    # look for geographic database
    if pg_services:
        # check if at least one pg_service name is referenced
        pg_services = check_usable_pg_services(requested_pg_services=pg_services)
        if not len(pg_services):
            logger.error("None of the specified pg_services is available.")
            raise typer.Exit(1)

        output_path = determine_output_path(
            output_path=output_path,
            output_format=output_format,
            pg_services=pg_services,
        )

        output_serializer = MetadatasetSerializerBase.get_serializer_from_parameters(
            format_or_serializer=output_format,
            output_path=output_path,
            opt_prettify_size=opt_prettify_size,
            opt_raw_path=opt_raw_path,
        )

        print("Start looking for geographic table in PostGIS...")
        # configure output workbook
        output_serializer.pre_serializing(has_sgbd=True)

        for pg_service in pg_services:
            print(f"Start processing using PostgreSQL service: {pg_service}")

            # testing connection settings
            sgbd_reader = ReadPostGIS(service=pg_service)
            sgbd_reader.get_connection()

            # check connection state
            if sgbd_reader.conn is None:
                fail_reason = sgbd_reader.db_connection.state_msg
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
                metadataset = sgbd_reader.infos_dataset(layer=layer)
                logger.info(f"Table examined: {metadataset.name}")
                output_serializer.serialize_metadaset(metadataset=metadataset)
                logger.debug("Layer metadata stored into workbook.")

        output_serializer.post_serializing()

        send_system_notify(
            notification_title="DicoGIS analysis ended",
            notification_message="DicoGIS successfully processed "
            f"{sgbd_reader.conn.GetLayerCount()} PostGIS tables. "
            "\nOpen the application to save the workbook.",
            notification_sound=opt_notify_sound,
        )

        if opt_open_output:
            typer.launch(url=f"{output_path.resolve()}")

    logger.info(f"Logs stored in {Path(app_dir).joinpath('logs')}")
