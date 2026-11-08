#! python3  # noqa: E265

"""Contract of the HTTP clients: what the publication code expects from the network.

Depends on neither requests nor Qt, in the same spirit as
dicogis.utils.progress.ProgressReporter: the backends implement it, the publication
code only knows about it.
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# Standard library
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol, runtime_checkable


if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


# ##############################################################################
# ########## Classes ###############
# ##################################


class HttpError(Exception):
    """Base class of the errors raised by the HTTP clients."""


class HttpTransportError(HttpError):
    """No HTTP response was received: connection refused, timeout, canceled..."""


class HttpStatusError(HttpError):
    """An HTTP response was received, telling an error.

    Attributes:
        response: the response at stake
    """

    def __init__(self, response: HttpResponse) -> None:
        """Build the error from its response.

        Args:
            response: the response at stake
        """
        super().__init__(f"HTTP error {response.status_code} for url: {response.url}")
        self.response = response


@dataclass
class HttpResponse:
    """An HTTP response, whatever the backend which received it.

    Attributes:
        status_code: HTTP status code
        headers: headers, names in lowercase
        cookies: cookies set by this very response, by name
        content: body
        url: final URL of the request
    """

    status_code: int
    headers: dict[str, str] = field(default_factory=dict)
    cookies: dict[str, str] = field(default_factory=dict)
    content: bytes = b""
    url: str = ""

    @property
    def text(self) -> str:
        """Body as text.

        Returns:
            decoded body, undecodable bytes being replaced
        """
        return self.content.decode("UTF-8", errors="replace")

    def json(self) -> object:
        """Decode the body as JSON.

        Returns:
            decoded body
        """
        return json.loads(self.content)

    def raise_for_status(self) -> None:
        """Raise an error if the response tells one.

        Raises:
            HttpStatusError: if the status code is 400 or above
        """
        if self.status_code >= 400:
            raise HttpStatusError(self)


@runtime_checkable
class HttpClient(Protocol):
    """What the publication code needs to reach a catalog.

    Implementations are stateless, cookies included: what a request sends is what its
    caller gives. Each backend otherwise has its own cookie jar, which overrides the
    Cookie header once it holds a cookie for the host.
    """

    def request(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, str | Sequence[str]] | None = None,
        headers: Mapping[str, str] | None = None,
        data: bytes | None = None,
        timeout: float | None = None,
    ) -> HttpResponse:
        """Send a request and wait for its response, redirections being followed.

        Args:
            method: HTTP method: GET, POST, PUT or DELETE
            url: URL, without its query string
            params: query string. A sequence repeats the parameter.
            headers: request headers
            data: body
            timeout: seconds to wait for the server

        Raises:
            HttpTransportError: if no response was received

        Returns:
            response, whatever its status code
        """
        ...


# ##############################################################################
# ########## Functions #############
# ##################################


def parse_set_cookie(header_value: str) -> dict[str, str]:
    """Read the cookies of Set-Cookie headers merged on several lines, as Qt does.

    Args:
        header_value: value of the Set-Cookie header

    Returns:
        cookies values, by name, without their attributes
    """
    cookies: dict[str, str] = {}
    for line in header_value.splitlines():
        name, separator, value = line.split(";", 1)[0].partition("=")
        if separator and name.strip():
            cookies[name.strip()] = value.strip()
    return cookies
