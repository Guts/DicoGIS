#! python3  # noqa: E265

"""Publication of DicoGIS metadata to a uData catalog.

UI-agnostic core shared by the `dicogis-cli publish` command and the GUI's
"Publish" tab: it depends on neither Typer nor Qt.
"""

# ############################################################################
# ########## Libraries #############
# ##################################

# standard lib
import json
import logging
from dataclasses import dataclass
from pathlib import Path

# project
from dicogis.publishing.report import PublishReport
from dicogis.publishing.settings import get_publish_timeout
from dicogis.utils.http import HttpClient, get_http_client
from dicogis.utils.progress import ProgressReporter


# ############################################################################
# ########## Globals ###############
# ##################################

logger = logging.getLogger(__name__)

# ############################################################################
# ########## Classes ###############
# ##################################


@dataclass
class _UdataApi:
    """How to reach a uData instance."""

    http_client: HttpClient
    api_key: str
    url_base: str
    version: str
    organization_id: str | None
    timeout: float

    def url(self, path: str) -> str:
        """Build the URL of an API route.

        Args:
            path: path of the route, from the API version

        Returns:
            full URL
        """
        return f"{self.url_base}{self.version}/{path}"

    @property
    def headers(self) -> dict[str, str]:
        """Headers of the requests.

        Returns:
            content type and API key
        """
        return {"Content-Type": "application/json", "X-API-KEY": self.api_key}


# ############################################################################
# ########## Functions #############
# ##################################


def _dicogis_extras(dataset_payload: object) -> dict:
    """Return the "extras" mapping of a uData dataset payload.

    Both the JSON files found on disk and the datasets returned by the catalog
    go through here, and neither is guaranteed to carry an "extras" object: a
    hand-written JSON file, or any dataset in the catalog not published by
    DicoGIS, simply has none.

    Args:
        dataset_payload: decoded JSON of a uData dataset, of any shape

    Returns:
        the "extras" mapping, or an empty one when absent or not a mapping
    """
    if not isinstance(dataset_payload, dict):
        return {}
    extras = dataset_payload.get("extras")
    return extras if isinstance(extras, dict) else {}


def _fetch_already_published(api: _UdataApi) -> tuple[tuple, tuple]:
    """Retrieve slugs and DicoGIS signatures already published to the target
    catalog, to avoid publishing duplicates.

    Args:
        api: uData instance, whose organization, if set, is looked at instead of the
            API-key owner.

    Returns:
        already published slugs, already published DicoGIS signatures.
    """
    route = (
        f"organizations/{api.organization_id}/datasets/"
        if api.organization_id
        else "me/datasets/"
    )
    response = api.http_client.request(
        "GET",
        api.url(route),
        params={"page_size": "100"},
        headers=api.headers,
        timeout=api.timeout,
    )
    response.raise_for_status()
    if api.organization_id:
        # be careful: this route stores the list in a 'data' attribute key
        already_published_datasets = response.json().get("data")
    else:
        already_published_datasets = response.json()

    # empty values are dropped: kept in, a missing slug/signature on the catalog
    # side would compare equal to a missing one on ours and wrongly mark the
    # file as already published
    already_published_slugs: list[str] = []
    already_published_signatures: list[str] = []
    for published_dataset in already_published_datasets or []:
        if slug := (
            published_dataset.get("slug")
            if isinstance(published_dataset, dict)
            else None
        ):
            already_published_slugs.append(slug)
        if signature := _dicogis_extras(published_dataset).get("dicogis_signature"):
            already_published_signatures.append(signature)

    return tuple(already_published_slugs), tuple(already_published_signatures)


def _publish_json_file(
    json_file: Path,
    report: PublishReport,
    api: _UdataApi,
    already_published_slugs: tuple,
    already_published_signatures: tuple,
    verbose: bool,
) -> None:
    """Publish one metadata JSON file, unless it isn't DicoGIS' or is already
    published, and count the outcome into the report.

    Args:
        json_file: metadata JSON file (udata flavor) to publish.
        report: run report, updated with this file's outcome.
        api: uData instance. If it has an organization, the dataset is added to it.
        already_published_slugs: slugs already in the catalog.
        already_published_signatures: DicoGIS signatures already in the catalog.
        verbose: log ignored files at info level.
    """
    # open it securely
    try:
        with json_file.open(mode="r", encoding="UTF-8") as f:
            data = json.load(f)

        if isinstance(data, dict) and api.organization_id:
            data["organization"] = {"id": api.organization_id}

    except Exception as err:
        err_msg = f"Impossible to load {json_file}. Trace: {err}"
        logger.error(err_msg)
        report.failed += 1
        report.errors.append(err_msg)
        return

    # filter out JSON files not related to DicoGIS
    metadataset_extras = _dicogis_extras(data)
    if not metadataset_extras.get("dicogis_version"):
        if verbose:
            logger.info(
                f"Looks like this file is not a metadataset from DicoGIS: {json_file}"
            )
        report.ignored += 1
        return

    # check if the metadata has been already published. Reaching this point
    # means data is a mapping: _dicogis_extras() returned something for it.
    dataset_slug = data.get("slug")
    dataset_signature = metadataset_extras.get("dicogis_signature")
    if (dataset_slug and dataset_slug in already_published_slugs) or (
        dataset_signature and dataset_signature in already_published_signatures
    ):
        if verbose:
            logger.info(
                f"JSON file {json_file} has the same slug or the same signature "
                "compared with an already published dataset. It's not gonna be "
                "published."
            )
        report.ignored += 1
        return

    # publish
    try:
        req_response = api.http_client.request(
            "POST",
            api.url("datasets"),
            headers=api.headers,
            data=json.dumps(data).encode("UTF-8"),
            timeout=api.timeout,
        )
        req_response.raise_for_status()
    except Exception as err:
        err_msg = f"Publish {json_file} to {api.url_base} failed. Trace: {err}"
        logger.error(err_msg)
        report.failed += 1
        report.errors.append(err_msg)
        return

    report.published += 1


def publish_metadata_folder(
    input_folder: Path,
    udata_api_key: str,
    udata_api_url_base: str = "https://demo.data.gouv.fr/api/",
    udata_api_version: str = "1",
    udata_organization_id: str | None = None,
    progress_reporter: ProgressReporter | None = None,
    verbose: bool = False,
    timeout: float | None = None,
    http_client: HttpClient | None = None,
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
        progress_reporter: told about each JSON file examined. Asking it to stop ends
            the run between two files, with a report of what was done until then.
        verbose: log ignored files (not DicoGIS or already published) at info level.
        timeout: seconds to wait for the catalog. Defaults to the
            DICOGIS_PUBLISH_TIMEOUT environment variable, or 30 seconds.
        http_client: HTTP client. Defaults to the one of the running environment.

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

    api = _UdataApi(
        http_client=http_client or get_http_client(),
        api_key=udata_api_key,
        url_base=udata_api_url_base,
        version=udata_api_version,
        organization_id=udata_organization_id,
        timeout=get_publish_timeout() if timeout is None else timeout,
    )

    # retrieve already published datasets to avoid duplicated publication
    already_published_slugs, already_published_signature = _fetch_already_published(api)

    report = PublishReport()
    if progress_reporter is not None:
        progress_reporter.set_total(len(li_json_files))

    for json_file in li_json_files:
        if progress_reporter is not None and progress_reporter.is_canceled():
            report.canceled = True
            break
        _publish_json_file(
            json_file=json_file,
            report=report,
            api=api,
            already_published_slugs=already_published_slugs,
            already_published_signatures=already_published_signature,
            verbose=verbose,
        )
        if progress_reporter is not None:
            progress_reporter.set_message(json_file.name)
            progress_reporter.increment()

    return report
