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


if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from dicogis.utils.http import HttpClient, HttpResponse, HttpStatusError


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
