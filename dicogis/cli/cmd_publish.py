#! python3  # noqa: E265

# ############################################################################
# ########## Libraries #############
# ##################################

# standard lib
import json
import logging
from pathlib import Path
from typing import Annotated

# 3rd party
import typer
from requests import Session
from rich.console import Console
from rich.progress import track

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

    # looking for JSON files
    li_json_files = list(input_folder.glob("*.json"))
    if not len(li_json_files):
        console_err.print(
            f":boom: [bold red]Error![/bold red] No JSON files found into {input_folder.resolve()}"
        )
        raise typer.Exit(code=1)

    if not udata_api_key:
        console_err.print(
            ":boom: [bold red]Error![/bold red] No API key defined for uData. "
            "Please set your API key as environment variable 'DICOGIS_UDATA_API_KEY'."
        )
        raise typer.Exit(code=1)

    # prepare http session
    req_session = Session()
    req_session.headers = {
        "Content-Type": "application/json",
        "X-API-KEY": udata_api_key,
    }

    # retrieve already published datasets to avoid duplicated publication
    if udata_organization_id:
        already_published_datasets = req_session.get(
            url=f"{udata_api_url_base}{udata_api_version}/organizations/"
            f"{udata_organization_id}/datasets/?page_size=100",
            allow_redirects=True,
        )
        already_published_datasets.raise_for_status()
        already_published_datasets = already_published_datasets.json().get(
            "data"
        )  # be careful: this route stores the list in a 'data' attribute key
    else:
        already_published_datasets = req_session.get(
            url=f"{udata_api_url_base}{udata_api_version}/me/datasets/?page_size=100",
            allow_redirects=True,
        )
        already_published_datasets.raise_for_status()
        already_published_datasets = already_published_datasets.json()

    already_published_slugs = tuple([d.get("slug") for d in already_published_datasets])
    already_published_signature = tuple(
        [
            d.get("extras", {}).get("dicogis_signature")
            for d in already_published_datasets
        ]
    )

    # counter and progress
    counter_correctly_published: int = 0
    counter_failed: int = 0
    counter_ignored: int = 0

    for json_file in track(li_json_files, description="Processing..."):
        # open it securely
        try:
            with json_file.open(mode="r", encoding="UTF-8") as f:
                data = json.load(f)

            if isinstance(data, dict) and udata_organization_id:
                data["organization"] = {"id": udata_organization_id}

        except Exception as err:
            err_msg = f"Impossible to load {json_file}. Trace: {err}"
            logger.error(err_msg)
            console_err.print(err_msg)
            counter_failed += 1
            continue

        # filter out JSON files not related to DicoGIS
        if not data.get("extras").get("dicogis_version"):
            logger.info(
                f"Looks like this file is not a metadataset from DicoGIS: {json_file}"
            )
            counter_ignored += 1
            continue

        # check if the metadata has been already published
        if (
            data.get("slugs") in already_published_slugs
            or data.get("extras", {}).get("dicogis_signature")
            in already_published_signature
        ):
            if verbose:
                console_out.print(
                    f"JSON file {json_file} has the same slug or the same signature "
                    f"compared with {len(already_published_datasets)} already published "
                    "datasets. It's not gonna be published."
                )
            counter_ignored += 1
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
            console_err.print(err_msg)
            counter_failed += 1
            continue

        counter_correctly_published += 1

    console_out.print(
        "==Publish report ==\n"
        f":white_check_mark: {counter_correctly_published} files published to "
        f"{udata_api_url_base}.\n"
        f":white_circle: {counter_ignored} files ignored.\n"
        f":red_square: {counter_failed} files failed."
    )

    send_system_notify(
        notification_title="DicoGIS publication ended",
        notification_message=f"{counter_correctly_published} published, "
        f"{counter_ignored} ignored,"
        f"{counter_failed} failed.",
        notification_sound=opt_notify_sound,
    )
