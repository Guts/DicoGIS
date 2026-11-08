#! python3  # noqa: E265

# ############################################################################
# ########## Libraries #############
# ##################################

# standard lib
import logging
from pathlib import Path
from typing import Annotated

# 3rd party
import typer
from rich.console import Console
from rich.progress import Progress

# project
from dicogis.__about__ import __package_name__
from dicogis.constants import (
    SUPPORTED_FORMATS,
    GeonetworkUpdateModes,
    PublishTargets,
)
from dicogis.publishing import geonetwork, udata
from dicogis.publishing.geonetwork import GeonetworkAuthenticationError
from dicogis.publishing.report import PublishReport
from dicogis.publishing.settings import DEFAULT_PUBLISH_TIMEOUT
from dicogis.utils.app_dir import get_app_dir
from dicogis.utils.http import HttpError
from dicogis.utils.journalizer import LogManager
from dicogis.utils.notifier import send_system_notify


# ############################################################################
# ########## Globals ###############
# ##################################

console_out = Console()
console_err = Console(stderr=True)
default_formats = ",".join([f.name for f in SUPPORTED_FORMATS])
logger = logging.getLogger(__name__)
state = {"verbose": False}

# ############################################################################
# ########## Classes ###############
# ##################################


class RichProgressReporter:
    """ProgressReporter on top of a Rich progress bar. Nothing cancels it: Ctrl+C
    interrupts the command."""

    def __init__(self, progress: Progress) -> None:
        """Add a task to a progress bar.

        Args:
            progress: running Rich progress bar
        """
        self.progress = progress
        self.task_id = progress.add_task("Processing...", total=None)

    def set_message(self, message: str) -> None:
        """Update the description of the task."""
        self.progress.update(self.task_id, description=message)

    def increment(self, amount: int = 1) -> None:
        """Increment the progress counter."""
        self.progress.advance(self.task_id, amount)

    def set_total(self, total: int) -> None:
        """Set the total value of the progress counter."""
        self.progress.update(self.task_id, total=total)

    def is_canceled(self) -> bool:
        """Tell the operation has not been asked to stop."""
        return False


# ############################################################################
# ########## Functions #############
# ##################################


def _publish_to_udata(
    input_folder: Path,
    progress_reporter: RichProgressReporter,
    api_key: str | None,
    api_url_base: str,
    api_version: str,
    organization_id: str | None,
    timeout: float,
    verbose: bool,
) -> PublishReport:
    """Publish a folder to a uData catalog, asking for the API key if it's unset.

    Args:
        input_folder: folder of the JSON files
        progress_reporter: told about the progress
        api_key: API key of the account
        api_url_base: API URL of the instance
        api_version: API version of the instance
        organization_id: organization to add the datasets to
        timeout: seconds to wait for the catalog
        verbose: log ignored files

    Returns:
        report of the run
    """
    if api_key is None:
        progress_reporter.progress.stop()
        api_key = typer.prompt(
            "uData API key", hide_input=True, confirmation_prompt=True
        )
        progress_reporter.progress.start()
    return udata.publish_metadata_folder(
        input_folder=input_folder,
        udata_api_key=api_key,
        udata_api_url_base=api_url_base,
        udata_api_version=api_version,
        udata_organization_id=organization_id,
        progress_reporter=progress_reporter,
        verbose=verbose,
        timeout=timeout,
    )


def _publish_to_geonetwork(
    input_folder: Path,
    progress_reporter: RichProgressReporter,
    url_base: str | None,
    portal: str,
    username: str | None,
    password: str | None,
    group: str | None,
    categories: str | None,
    update_mode: GeonetworkUpdateModes,
    publish_to_all: bool,
    reject_if_invalid: bool,
    timeout: float,
) -> PublishReport:
    """Publish a folder to a GeoNetwork catalog, asking for the account if it's unset.

    Args:
        input_folder: folder of the XML files
        progress_reporter: told about the progress
        url_base: URL of the instance
        portal: portal of the instance
        username: name of the account
        password: password of the account
        group: identifier of the group of the records
        categories: identifiers of the categories of the records, comma separated
        update_mode: what to do with a record the catalog already has
        publish_to_all: make the records visible to everyone
        reject_if_invalid: have the catalog refuse the invalid records
        timeout: seconds to wait for the catalog

    Returns:
        report of the run
    """
    if username is None or password is None:
        progress_reporter.progress.stop()
        username = username or typer.prompt("GeoNetwork username")
        password = password or typer.prompt("GeoNetwork password", hide_input=True)
        progress_reporter.progress.start()
    return geonetwork.publish_metadata_folder(
        input_folder=input_folder,
        url_base=url_base or "",
        group=group or "",
        credentials=geonetwork.GeonetworkCredentials(username, password),
        portal=portal,
        categories=[
            category.strip()
            for category in (categories or "").split(",")
            if category.strip()
        ],
        update_mode=update_mode,
        publish_to_all=publish_to_all,
        reject_if_invalid=reject_if_invalid,
        timeout=timeout,
        progress_reporter=progress_reporter,
    )


def publish(
    input_folder: Annotated[
        Path | None,
        typer.Option(
            dir_okay=True,
            envvar="DICOGIS_PUBLISH_INPUT_FOLDER",
            file_okay=False,
            help="Folder where are stored the metadata to publish: JSON files (udata "
            "flavor) for uData, ISO 19139 XML files for GeoNetwork.",
            exists=True,
            readable=True,
            resolve_path=True,
        ),
    ] = None,
    target: Annotated[
        PublishTargets,
        typer.Option(
            case_sensitive=False,
            envvar="DICOGIS_PUBLISH_TARGET",
            help="Kind of catalog to publish to.",
        ),
    ] = PublishTargets.udata,
    udata_api_key: Annotated[
        str | None,
        typer.Option(
            envvar="DICOGIS_UDATA_API_KEY",
            help="API key of the account uData instance. Asked for if not set.",
        ),
    ] = None,
    udata_api_url_base: Annotated[
        str | None,
        typer.Option(
            envvar="DICOGIS_UDATA_API_URL_BASE",
            help="API URL of the uData instance.",
        ),
    ] = "https://demo.data.gouv.fr/api/",
    udata_api_version: Annotated[
        str | None,
        typer.Option(
            envvar="DICOGIS_UDATA_API_VERSION",
            help="API's version of the uData instance.",
        ),
    ] = "1",
    udata_organization_id: Annotated[
        str | None,
        typer.Option(
            envvar="DICOGIS_UDATA_ORGANIZATION_ID",
            help="Organization ID in uData instance. If set, datasets will be added to "
            "the organization instead of the user authenticated with the API key.",
        ),
    ] = None,
    geonetwork_url_base: Annotated[
        str | None,
        typer.Option(
            envvar="DICOGIS_GEONETWORK_URL_BASE",
            help="URL of the GeoNetwork instance. Example: "
            "https://catalogue.example/geonetwork",
        ),
    ] = None,
    geonetwork_portal: Annotated[
        str,
        typer.Option(
            envvar="DICOGIS_GEONETWORK_PORTAL",
            help="Portal (sub-catalog) of the GeoNetwork instance.",
        ),
    ] = "srv",
    geonetwork_username: Annotated[
        str | None,
        typer.Option(
            envvar="DICOGIS_GEONETWORK_USERNAME",
            help="Name of an account of the GeoNetwork instance, at least Editor. "
            "Asked for if not set.",
        ),
    ] = None,
    geonetwork_password: Annotated[
        str | None,
        typer.Option(
            envvar="DICOGIS_GEONETWORK_PASSWORD",
            help="Password of the account. Asked for if not set.",
        ),
    ] = None,
    geonetwork_group: Annotated[
        str | None,
        typer.Option(
            envvar="DICOGIS_GEONETWORK_GROUP",
            help="Numeric identifier of the group the records are attached to. "
            "Mandatory for GeoNetwork.",
        ),
    ] = None,
    geonetwork_categories: Annotated[
        str | None,
        typer.Option(
            envvar="DICOGIS_GEONETWORK_CATEGORIES",
            help="Identifiers of the categories of the records, comma separated.",
        ),
    ] = None,
    geonetwork_update_mode: Annotated[
        GeonetworkUpdateModes,
        typer.Option(
            case_sensitive=False,
            envvar="DICOGIS_GEONETWORK_UPDATE_MODE",
            help="What to do with a record the catalog already has: overwrite replaces "
            "it, complete only fills its empty fields.",
        ),
    ] = GeonetworkUpdateModes.overwrite,
    geonetwork_publish_to_all: Annotated[
        bool,
        typer.Option(
            envvar="DICOGIS_GEONETWORK_PUBLISH_TO_ALL",
            help="Make the records visible to everyone.",
        ),
    ] = False,
    geonetwork_reject_if_invalid: Annotated[
        bool,
        typer.Option(
            envvar="DICOGIS_GEONETWORK_REJECT_IF_INVALID",
            help="Have the catalog refuse the records invalid against the XSD.",
        ),
    ] = False,
    timeout: Annotated[
        float,
        typer.Option(
            envvar="DICOGIS_PUBLISH_TIMEOUT",
            help="Seconds to wait for the catalog before giving up on a request.",
            min=1,
        ),
    ] = DEFAULT_PUBLISH_TIMEOUT,
    opt_notify_sound: Annotated[
        bool,
        typer.Option(
            envvar="DICOGIS_ENABLE_NOTIFICATION_SOUND",
            help="Enable/disable notification's sound at the end of processing.",
        ),
    ] = True,
    verbose: Annotated[
        bool,
        typer.Option(
            envvar="DICOGIS_DEBUG",
            help="Increase verbosity to show debug logs.",
        ),
    ] = False,
):
    """Publish metadata (previously exported as files) to a catalog."""
    app_dir = get_app_dir()
    # start logging
    if verbose:
        state["verbose"] = True

    logmngr = LogManager(
        console_level=logging.DEBUG if verbose else logging.WARNING,
        file_level=logging.DEBUG if verbose else logging.WARNING,
        label=f"{__package_name__}-cli-publish",
        folder=Path(app_dir).joinpath("logs"),
    )
    # add headers
    logmngr.headers()
    logger.debug(f"DicoGIS working folder: {app_dir}")
    logger.debug(f"CLI passed parameters: {input_folder=} - {target=} - {verbose=}")

    # check minimal parameters: the option defaults to None, and
    # publish_metadata_folder() would otherwise fail on `None.glob()`
    if input_folder is None:
        console_err.print(
            ":boom: [bold red]Error![/bold red] No input folder specified. Use "
            "--input-folder, or set the DICOGIS_PUBLISH_INPUT_FOLDER environment "
            "variable, to point at the folder holding the files to publish."
        )
        raise typer.Exit(code=1)

    target = PublishTargets(target)
    try:
        with Progress(console=console_out) as progress:
            progress_reporter = RichProgressReporter(progress)
            if target == PublishTargets.geonetwork:
                catalog_url = geonetwork_url_base
                report = _publish_to_geonetwork(
                    input_folder=input_folder,
                    progress_reporter=progress_reporter,
                    url_base=geonetwork_url_base,
                    portal=geonetwork_portal,
                    username=geonetwork_username,
                    password=geonetwork_password,
                    group=geonetwork_group,
                    categories=geonetwork_categories,
                    update_mode=geonetwork_update_mode,
                    publish_to_all=geonetwork_publish_to_all,
                    reject_if_invalid=geonetwork_reject_if_invalid,
                    timeout=timeout,
                )
            else:
                catalog_url = udata_api_url_base
                report = _publish_to_udata(
                    input_folder=input_folder,
                    progress_reporter=progress_reporter,
                    api_key=udata_api_key,
                    api_url_base=udata_api_url_base,
                    api_version=udata_api_version,
                    organization_id=udata_organization_id,
                    timeout=timeout,
                    verbose=verbose,
                )
    except (
        FileNotFoundError,
        ValueError,
        GeonetworkAuthenticationError,
        HttpError,
    ) as err:
        console_err.print(f":boom: [bold red]Error![/bold red] {err}")
        raise typer.Exit(code=1) from err

    console_out.print(
        "==Publish report ==\n"
        f":white_check_mark: {report.published} files published to "
        f"{catalog_url}.\n"
        f":white_circle: {report.ignored} files ignored.\n"
        f":red_square: {report.failed} files failed."
    )
    if report.up_to_date:
        console_out.print(
            f":white_check_mark: {report.up_to_date} records already complete."
        )
    for file_name, added_fields in report.added_fields.items():
        console_out.print(f"{file_name}: added {', '.join(added_fields)}.")
    for error_message in report.errors:
        console_err.print(error_message, markup=False)

    send_system_notify(
        notification_title="DicoGIS publication ended",
        notification_message=f"{report.published} published, "
        f"{report.ignored} ignored,"
        f"{report.failed} failed.",
        notification_sound=opt_notify_sound,
    )
