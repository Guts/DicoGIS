#! python3  # noqa: E265

# ############################################################################
# ########## Libraries #############
# ##################################

# standard lib
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated

# 3rd party
import typer
from requests import Session
from rich.console import Console
from rich.progress import Progress

# project
from dicogis.__about__ import __package_name__, __title__
from dicogis.constants import SUPPORTED_FORMATS
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


@dataclass
class PublishReport:
    """Outcome of a publish_metadata_folder() run."""

    published: int = 0
    ignored: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        """Total number of JSON files examined."""
        return self.published + self.ignored + self.failed


# ############################################################################
# ########## Functions #############
# ##################################


def _fetch_already_published(
    req_session: Session,
    udata_api_url_base: str,
    udata_api_version: str,
    udata_organization_id: str | None,
) -> tuple[tuple, tuple]:
    """Retrieve slugs and DicoGIS signatures already published to the target
    catalog, to avoid publishing duplicates.

    Args:
        req_session: pre-configured HTTP session (with auth headers set).
        udata_api_url_base: base API URL of the uData instance.
        udata_api_version: API version of the uData instance.
        udata_organization_id: if set, look at this organization's datasets
            instead of the API-key owner's ones.

    Returns:
        already published slugs, already published DicoGIS signatures.
    """
    if udata_organization_id:
        response = req_session.get(
            url=f"{udata_api_url_base}{udata_api_version}/organizations/"
            f"{udata_organization_id}/datasets/?page_size=100",
            allow_redirects=True,
        )
        response.raise_for_status()
        # be careful: this route stores the list in a 'data' attribute key
        already_published_datasets = response.json().get("data")
    else:
        response = req_session.get(
            url=f"{udata_api_url_base}{udata_api_version}/me/datasets/?page_size=100",
            allow_redirects=True,
        )
        response.raise_for_status()
        already_published_datasets = response.json()

    already_published_slugs = tuple(d.get("slug") for d in already_published_datasets)
    already_published_signatures = tuple(
        d.get("extras", {}).get("dicogis_signature") for d in already_published_datasets
    )
    return already_published_slugs, already_published_signatures


def publish_metadata_folder(
    input_folder: Path,
    udata_api_key: str,
    udata_api_url_base: str = "https://demo.data.gouv.fr/api/",
    udata_api_version: str = "1",
    udata_organization_id: str | None = None,
    progress_callback: Callable[[int, int, Path], None] | None = None,
    verbose: bool = False,
) -> PublishReport:
    """Publish every DicoGIS metadata JSON file within a folder to a uData catalog.

    This is the core, UI-agnostic logic shared by the `dicogis-cli publish` command
    and the GUI's "Publish" tab.

    Args:
        input_folder: folder where metadata JSON files (udata flavor) are stored.
        udata_api_key: API key of the account on the uData instance.
        udata_api_url_base: API URL of the uData instance.
        udata_api_version: API version of the uData instance.
        udata_organization_id: organization ID in the uData instance. If set,
            datasets are added to the organization instead of the user
            authenticated with the API key.
        progress_callback: called after each JSON file has been examined, with
            (files_done, files_total, current_json_file).
        verbose: log ignored files (not DicoGIS or already published) at info level.

    Raises:
        FileNotFoundError: if input_folder contains no JSON file.
        ValueError: if udata_api_key is empty.

    Returns:
        counters and per-file error messages for the run.
    """
    li_json_files = list(input_folder.glob("*.json"))
    if not len(li_json_files):
        raise FileNotFoundError(f"No JSON files found into {input_folder.resolve()}")

    if not udata_api_key:
        raise ValueError("No API key defined for uData.")

    # prepare http session
    req_session = Session()
    req_session.headers = {
        "Content-Type": "application/json",
        "X-API-KEY": udata_api_key,
    }

    # retrieve already published datasets to avoid duplicated publication
    already_published_slugs, already_published_signature = _fetch_already_published(
        req_session=req_session,
        udata_api_url_base=udata_api_url_base,
        udata_api_version=udata_api_version,
        udata_organization_id=udata_organization_id,
    )

    report = PublishReport()
    files_total = len(li_json_files)

    for files_done, json_file in enumerate(li_json_files, start=1):
        # open it securely
        try:
            with json_file.open(mode="r", encoding="UTF-8") as f:
                data = json.load(f)

            if isinstance(data, dict) and udata_organization_id:
                data["organization"] = {"id": udata_organization_id}

        except Exception as err:
            err_msg = f"Impossible to load {json_file}. Trace: {err}"
            logger.error(err_msg)
            report.failed += 1
            report.errors.append(err_msg)
            if progress_callback:
                progress_callback(files_done, files_total, json_file)
            continue

        # filter out JSON files not related to DicoGIS
        if not data.get("extras").get("dicogis_version"):
            if verbose:
                logger.info(
                    f"Looks like this file is not a metadataset from DicoGIS: {json_file}"
                )
            report.ignored += 1
            if progress_callback:
                progress_callback(files_done, files_total, json_file)
            continue

        # check if the metadata has been already published
        if (
            data.get("slug") in already_published_slugs
            or data.get("extras", {}).get("dicogis_signature")
            in already_published_signature
        ):
            if verbose:
                logger.info(
                    f"JSON file {json_file} has the same slug or the same signature "
                    "compared with an already published dataset. It's not gonna be "
                    "published."
                )
            report.ignored += 1
            if progress_callback:
                progress_callback(files_done, files_total, json_file)
            continue

        # publish
        try:
            req_response = req_session.post(
                url=f"{udata_api_url_base}{udata_api_version}/datasets", json=data
            )
            req_response.raise_for_status()
        except Exception as err:
            err_msg = (
                f"Publish {json_file} to {udata_api_url_base} failed. Trace: {err}"
            )
            logger.error(err_msg)
            report.failed += 1
            report.errors.append(err_msg)
            if progress_callback:
                progress_callback(files_done, files_total, json_file)
            continue

        report.published += 1
        if progress_callback:
            progress_callback(files_done, files_total, json_file)

    return report


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
            is_flag=True,
            help="Enable/disable notification's sound at the end of processing.",
        ),
    ] = True,
    verbose: bool = False,
):
    """Publish metadata (previously exported as JSON files) to a catalog."""
    app_dir = typer.get_app_dir(app_name=__title__, force_posix=True)
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
