#! python3  # noqa: E265

"""HTTP client based on requests: the CLI and the standalone GUI."""

# ##############################################################################
# ########## Libraries #############
# ##################################

# Standard library
from __future__ import annotations

from http.cookiejar import DefaultCookiePolicy
from typing import TYPE_CHECKING

# 3rd party
from requests import RequestException, Session

# project
from dicogis.utils.http.client import HttpResponse, HttpTransportError


if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


# ##############################################################################
# ########## Classes ###############
# ##################################


class RequestsHttpClient:
    """HTTP client based on a requests session, for its connections pooling."""

    def __init__(self) -> None:
        """Initialize the session, which stores no cookie: see HttpClient."""
        self.session = Session()
        self.session.cookies.set_policy(DefaultCookiePolicy(allowed_domains=[]))

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
        """Send a request and wait for its response. See HttpClient.request().

        Args:
            method: HTTP method
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
        try:
            response = self.session.request(
                method,
                url,
                params=params,
                headers=dict(headers) if headers else None,
                data=data,
                timeout=timeout,
            )
        except RequestException as err:
            raise HttpTransportError(f"{method} {url} failed: {err}") from err

        return HttpResponse(
            status_code=response.status_code,
            headers={name.lower(): value for name, value in response.headers.items()},
            cookies=response.cookies.get_dict(),
            content=response.content,
            url=response.url,
        )
