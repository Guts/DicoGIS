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
from dicogis.constants import SUPPORTED_FORMATS
from dicogis.publishing.udata import publish_metadata_folder
from dicogis.utils.app_dir import get_app_dir
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
# ########## Functions #############
# ##################################


def publish(
    input_folder: Annotated[
        Path | None,
        typer.Option(
            dir_okay=True,
            envvar="DICOGIS_PUBLISH_INPUT_FOLDER",
            file_okay=False,
            help="Folder where are stored metadata as JSON files to publish.",
            exists=True,
            readable=True,
            resolve_path=True,
        ),
    ] = None,
    udata_api_key: Annotated[
        str | None,
        typer.Option(
            envvar="DICOGIS_UDATA_API_KEY",
            help="API key of the account uData instance.",
            prompt=True,
            confirmation_prompt=True,
            hide_input=True,
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
    """Publish metadata (previously exported as JSON files) to a catalog."""
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
    logger.debug(f"CLI passed parameters: {input_folder=} - {verbose=}")

    # check minimal parameters: the option defaults to None, and
    # publish_metadata_folder() would otherwise fail on `None.glob()`
    if input_folder is None:
        console_err.print(
            ":boom: [bold red]Error![/bold red] No input folder specified. Use "
            "--input-folder, or set the DICOGIS_PUBLISH_INPUT_FOLDER environment "
            "variable, to point at the folder holding the JSON files to publish."
        )
        raise typer.Exit(code=1)

    try:
        with Progress(console=console_out) as progress:
            task_id = progress.add_task("Processing...", total=None)

            def _on_progress(
                files_done: int, files_total: int, current_file: Path
            ) -> None:
                progress.update(task_id, total=files_total, completed=files_done)

            report = publish_metadata_folder(
                input_folder=input_folder,
                udata_api_key=udata_api_key,
                udata_api_url_base=udata_api_url_base,
                udata_api_version=udata_api_version,
                udata_organization_id=udata_organization_id,
                progress_callback=_on_progress,
                verbose=verbose,
            )
    except FileNotFoundError as err:
        console_err.print(f":boom: [bold red]Error![/bold red] {err}")
        raise typer.Exit(code=1) from err
    except ValueError as err:
        console_err.print(
            f":boom: [bold red]Error![/bold red] {err} "
            "Please set your API key as environment variable 'DICOGIS_UDATA_API_KEY'."
        )
        raise typer.Exit(code=1) from err

    console_out.print(
        "==Publish report ==\n"
        f":white_check_mark: {report.published} files published to "
        f"{udata_api_url_base}.\n"
        f":white_circle: {report.ignored} files ignored.\n"
        f":red_square: {report.failed} files failed."
    )

    send_system_notify(
        notification_title="DicoGIS publication ended",
        notification_message=f"{report.published} published, "
        f"{report.ignored} ignored,"
        f"{report.failed} failed.",
        notification_sound=opt_notify_sound,
    )
