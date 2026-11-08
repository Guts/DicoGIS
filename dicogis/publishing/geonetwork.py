#! python3  # noqa: E265

"""Publication of ISO 19139 metadata to a GeoNetwork 4.4 catalog, through its REST API.

UI-agnostic core shared by the `dicogis-cli publish` command and the GUI's "Publish"
tab: it depends on neither Typer nor Qt.
"""

# ############################################################################
# ########## Libraries #############
# ##################################

# standard lib
from __future__ import annotations

import base64
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING
from urllib.parse import quote

# 3rd party
from lxml import etree

# project
from dicogis.constants import GeonetworkUpdateModes
from dicogis.export.to_iso19139 import (
    ISO19139_NAMESPACES,
    complete_record,
    is_iso19139_record,
    safe_xml_parser,
)
from dicogis.publishing.report import PublishReport
from dicogis.publishing.settings import get_publish_timeout
from dicogis.utils.http import HttpError, HttpStatusError, get_http_client


if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from dicogis.utils.http import HttpClient, HttpResponse
    from dicogis.utils.progress import ProgressReporter


# ############################################################################
# ########## Globals ###############
# ##################################

logger = logging.getLogger(__name__)

XSRF_COOKIE: str = "XSRF-TOKEN"

# ############################################################################
# ########## Classes ###############
# ##################################


class GeonetworkAuthenticationError(Exception):
    """The catalog can't be written to with what was given: nothing can be published."""


@dataclass(frozen=True)
class GeonetworkCredentials:
    """Account on a GeoNetwork instance. Its profile must be at least Editor."""

    username: str
    password: str

    def __repr__(self) -> str:
        """Leave the password out of logs and tracebacks.

        Returns:
            representation of the credentials
        """
        return f"GeonetworkCredentials(username={self.username!r})"


@dataclass(frozen=True)
class _Options:
    """How to publish the records."""

    group: str
    categories: tuple[str, ...] = ()
    update_mode: GeonetworkUpdateModes = GeonetworkUpdateModes.overwrite
    publish_to_all: bool = False
    reject_if_invalid: bool = False


class GeonetworkSession:
    """Authenticated exchanges with a GeoNetwork instance.

    GeoNetwork keeps its CSRF token in a cookie: each write must send it back both as
    this cookie and in the X-XSRF-TOKEN header. Handled here rather than left to the
    cookie jar of the HTTP clients, which behave differently and may hold the session
    of something else within QGIS.
    """

    def __init__(
        self,
        http_client: HttpClient,
        url_base: str,
        portal: str = "srv",
        credentials: GeonetworkCredentials | None = None,
        timeout: float | None = None,
    ) -> None:
        """Prepare the session.

        Args:
            http_client: HTTP client
            url_base: URL of the instance, e.g. https://catalogue.example/geonetwork
            portal: portal (sub-catalog) of the instance
            credentials: account to log in with. None when the HTTP client handles the
                authentication itself (authentication configuration of QGIS).
            timeout: seconds to wait for the catalog
        """
        self.http_client = http_client
        self.url_base = url_base.rstrip("/")
        self.portal = portal
        self.credentials = credentials
        self.timeout = timeout
        self.cookies: dict[str, str] = {}

    def api_url(self, route: str) -> str:
        """Build the URL of an API route.

        Args:
            route: path of the route, from the API root

        Returns:
            full URL
        """
        return f"{self.url_base}/{self.portal}/api/{route}"

    def _headers(self, extra: Mapping[str, str] | None = None) -> dict[str, str]:
        """Build the headers of a request: authentication, cookies and CSRF token.

        Args:
            extra: other headers of the request

        Returns:
            headers
        """
        headers = dict(extra or {})
        if self.credentials is not None:
            basic_token = base64.b64encode(
                f"{self.credentials.username}:{self.credentials.password}".encode()
            ).decode("ascii")
            headers["Authorization"] = f"Basic {basic_token}"
        if self.cookies:
            headers["Cookie"] = "; ".join(
                f"{name}={value}" for name, value in self.cookies.items()
            )
        if XSRF_COOKIE in self.cookies:
            headers["X-XSRF-TOKEN"] = self.cookies[XSRF_COOKIE]
        return headers

    def request(
        self,
        method: str,
        route: str,
        *,
        params: Mapping[str, str | Sequence[str]] | None = None,
        headers: Mapping[str, str] | None = None,
        data: bytes | None = None,
    ) -> HttpResponse:
        """Send an authenticated request.

        Args:
            method: HTTP method
            route: path of the API route
            params: query string
            headers: other headers of the request
            data: body

        Raises:
            HttpTransportError: if no response was received

        Returns:
            response, whatever its status code
        """
        response = self.http_client.request(
            method,
            self.api_url(route),
            params=params,
            headers=self._headers(headers),
            data=data,
            timeout=self.timeout,
        )
        # the token may be renewed along the way
        self.cookies.update(response.cookies)
        return response

    def open(self) -> None:
        """Check the account and retrieve the CSRF token.

        Raises:
            GeonetworkAuthenticationError: if the account isn't logged in, or the
                instance gives no token
            HttpTransportError: if the instance can't be reached
        """
        response = self.request("GET", "me", headers={"Accept": "application/json"})
        if response.status_code == 204:
            raise GeonetworkAuthenticationError(
                f"{self.url_base} considers this client as anonymous: check the "
                "credentials."
            )
        if response.status_code != 200:
            raise GeonetworkAuthenticationError(
                f"Logging in to {self.api_url('me')} failed with HTTP status "
                f"{response.status_code}: check the URL, the portal and the "
                "credentials."
            )
        if XSRF_COOKIE not in self.cookies:
            raise GeonetworkAuthenticationError(
                f"{self.url_base} gave no {XSRF_COOKIE} cookie: writing to it would be "
                "refused. Is it really a GeoNetwork 4.4?"
            )


# ############################################################################
# ########## Functions #############
# ##################################


def describe_http_error(error: HttpStatusError) -> str:
    """Tell what went wrong from the response of the catalog, which explains itself.

    Args:
        error: error to describe

    Returns:
        status code and beginning of the response
    """
    response = error.response
    return f"HTTP {response.status_code}: {response.text[:500]}"


def _upload_record(session: GeonetworkSession, xml: bytes, options: _Options) -> None:
    """Insert a record in the catalog, or replace the one with the same identifier.

    Args:
        session: open session
        xml: ISO 19139 document
        options: publication options

    Raises:
        HttpError: if the catalog refused the record or couldn't be reached
        ValueError: if the catalog accepted the request but reported an error
    """
    params: dict[str, str | Sequence[str]] = {
        "metadataType": "METADATA",
        "uuidProcessing": "OVERWRITE",
        "group": options.group,
        "publishToAll": str(options.publish_to_all).lower(),
        "rejectIfInvalid": str(options.reject_if_invalid).lower(),
    }
    if options.categories:
        params["category"] = list(options.categories)

    response = session.request(
        "PUT",
        "records",
        params=params,
        headers={"Content-Type": "application/xml", "Accept": "application/json"},
        data=xml,
    )
    response.raise_for_status()

    # some failures only show in the processing report of a successful response
    try:
        processing_report = response.json()
    except ValueError:
        logger.debug(f"Unexpected response of the catalog: {response.text[:500]}")
        return
    if isinstance(processing_report, dict) and (
        processing_report.get("numberOfRecordsWithErrors")
        or processing_report.get("errors")
    ):
        raise ValueError(f"Processing report: {response.text[:500]}")


def _fetch_record(session: GeonetworkSession, identifier: str) -> etree._Element | None:
    """Retrieve a record of the catalog as an editor sees it.

    `approved=false` gets the working copy when the workflow is enabled: it's the one
    an update goes to, whereas the approved version would ignore what editors did since.
    The popularity of a record must not grow because of DicoGIS looking at it.

    Args:
        session: open session
        identifier: identifier of the record

    Raises:
        HttpError: if the catalog refused to answer or couldn't be reached
        etree.XMLSyntaxError: if the catalog answered with something else than XML

    Returns:
        root of the record, or None if the catalog doesn't have it
    """
    response = session.request(
        "GET",
        f"records/{quote(identifier, safe='')}/formatters/xml",
        params={"approved": "false", "increasePopularity": "false"},
        headers={"Accept": "application/xml"},
    )
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return etree.fromstring(response.content, parser=safe_xml_parser())


def _complete_or_insert(
    session: GeonetworkSession,
    xml_file: Path,
    document: etree._Element,
    identifier: str,
    report: PublishReport,
    options: _Options,
) -> None:
    """Insert a record the catalog doesn't have, or fill the empty fields of its own.

    Args:
        session: open session
        xml_file: file holding the record
        document: root of the record
        identifier: identifier of the record
        report: run report, updated with this file's outcome
        options: publication options

    Raises:
        HttpError: if the catalog refused the record or couldn't be reached
        ValueError: if the catalog accepted the request but reported an error
        etree.XMLSyntaxError: if the catalog answered with something else than XML
    """
    remote = _fetch_record(session, identifier)
    if remote is None:
        _upload_record(session, xml_file.read_bytes(), options)
        report.published += 1
        return

    if not is_iso19139_record(remote):
        report.ignored += 1
        report.errors.append(
            f"The record of {xml_file} in the catalog isn't an ISO 19139 one "
            f"({etree.QName(remote).text}): it was left as is."
        )
        logger.warning(report.errors[-1])
        return

    completed, added_fields = complete_record(remote, document)
    if not added_fields:
        report.up_to_date += 1
        return

    _upload_record(
        session,
        etree.tostring(completed, encoding="UTF-8", xml_declaration=True),
        options,
    )
    report.published += 1
    report.added_fields[xml_file.name] = added_fields


def _publish_file(
    session: GeonetworkSession, xml_file: Path, report: PublishReport, options: _Options
) -> None:
    """Publish one XML file and count the outcome into the report.

    Args:
        session: open session
        xml_file: file to publish
        report: run report, updated with this file's outcome
        options: publication options
    """
    try:
        document = etree.parse(str(xml_file), parser=safe_xml_parser()).getroot()
    except (OSError, etree.XMLSyntaxError) as err:
        report.failed += 1
        report.errors.append(f"Impossible to load {xml_file}. Trace: {err}")
        logger.error(report.errors[-1])
        return

    if not is_iso19139_record(document):
        logger.info(f"Not an ISO 19139 record, ignored: {xml_file}")
        report.ignored += 1
        return

    identifier = document.findtext(
        "gmd:fileIdentifier/gco:CharacterString", namespaces=ISO19139_NAMESPACES
    )
    if not identifier or not identifier.strip():
        report.failed += 1
        report.errors.append(
            f"{xml_file} has no gmd:fileIdentifier: publishing it would make a new "
            "record each time."
        )
        logger.error(report.errors[-1])
        return

    try:
        if options.update_mode == GeonetworkUpdateModes.complete:
            _complete_or_insert(
                session, xml_file, document, identifier, report, options
            )
        else:
            _upload_record(session, xml_file.read_bytes(), options)
            report.published += 1
    except HttpStatusError as err:
        report.failed += 1
        report.errors.append(f"Publish {xml_file} failed. {describe_http_error(err)}")
        logger.error(report.errors[-1])
    except (HttpError, OSError, ValueError, etree.XMLSyntaxError) as err:
        report.failed += 1
        report.errors.append(f"Publish {xml_file} failed. Trace: {err}")
        logger.error(report.errors[-1])


def publish_metadata_folder(
    input_folder: Path,
    url_base: str,
    *,
    group: str,
    credentials: GeonetworkCredentials | None = None,
    portal: str = "srv",
    categories: Sequence[str] = (),
    update_mode: str = GeonetworkUpdateModes.overwrite,
    publish_to_all: bool = False,
    reject_if_invalid: bool = False,
    timeout: float | None = None,
    http_client: HttpClient | None = None,
    progress_reporter: ProgressReporter | None = None,
) -> PublishReport:
    """Publish every ISO 19139 file of a folder to a GeoNetwork 4.4 catalog.

    Args:
        input_folder: folder where the XML files are stored
        url_base: URL of the instance, e.g. https://catalogue.example/geonetwork
        group: identifier of the group the records are attached to. Mandatory:
            GeoNetwork 4.4 refuses an insertion without it.
        credentials: account to log in with. None when the HTTP client handles the
            authentication itself (authentication configuration of QGIS).
        portal: portal (sub-catalog) of the instance
        categories: identifiers of the categories of the records
        update_mode: what to do with a record the catalog already has: `overwrite`
            replaces it, `complete` only fills its empty fields, leaving what was
            changed by hand in the catalog as is.
        publish_to_all: make the records visible to everyone. Forced to false by
            GeoNetwork when its workflow is enabled.
        reject_if_invalid: have the catalog refuse the records invalid against the XSD
        timeout: seconds to wait for the catalog. Defaults to the
            DICOGIS_PUBLISH_TIMEOUT environment variable, or 30 seconds.
        http_client: HTTP client. Defaults to the one of the running environment.
        progress_reporter: told about each file examined. Asking it to stop ends the
            run between two files, with a report of what was done until then.

    Raises:
        FileNotFoundError: if input_folder contains no XML file
        ValueError: if the URL is missing, the group isn't an identifier or the update
            mode is unknown
        GeonetworkAuthenticationError: if the account can't write to the catalog
        HttpTransportError: if the catalog can't be reached

    Returns:
        counters and per-file error messages for the run
    """
    xml_files = sorted(input_folder.glob("*.xml"))
    if not xml_files:
        raise FileNotFoundError(f"No XML files found into {input_folder.resolve()}")
    if not url_base:
        raise ValueError("No URL defined for GeoNetwork.")
    if not str(group).strip().isdigit():
        raise ValueError(
            f"The GeoNetwork group must be given by its numeric identifier, got: "
            f"'{group}'."
        )

    options = _Options(
        group=str(group).strip(),
        categories=tuple(categories),
        update_mode=GeonetworkUpdateModes(update_mode),
        publish_to_all=publish_to_all,
        reject_if_invalid=reject_if_invalid,
    )
    session = GeonetworkSession(
        http_client=http_client or get_http_client(),
        url_base=url_base,
        portal=portal,
        credentials=credentials,
        timeout=get_publish_timeout() if timeout is None else timeout,
    )
    session.open()

    report = PublishReport()
    if progress_reporter is not None:
        progress_reporter.set_total(len(xml_files))

    for xml_file in xml_files:
        if progress_reporter is not None and progress_reporter.is_canceled():
            report.canceled = True
            break
        _publish_file(session, xml_file, report, options)
        if progress_reporter is not None:
            progress_reporter.set_message(xml_file.name)
            progress_reporter.increment()

    return report
