#! python3  # noqa: E265

"""HTTP client based on the network stack of QGIS.

Applies what is configured in QGIS (proxy, SSL exceptions, authentication manager) and
can run from any thread, typically in a QgsTask. QGIS is imported at the last moment:
this module must stay importable without it.
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# Standard library
from __future__ import annotations

from typing import TYPE_CHECKING

# project
from dicogis.utils.http.client import (
    HttpResponse,
    HttpTransportError,
    parse_set_cookie,
)


if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from qgis.core import QgsFeedback


# ##############################################################################
# ########## Classes ###############
# ##################################


class QgisHttpClient:
    """HTTP client based on QgsBlockingNetworkRequest."""

    def __init__(
        self, authcfg: str | None = None, feedback: QgsFeedback | None = None
    ) -> None:
        """Initialize the client.

        Args:
            authcfg: identifier of a configuration of the QGIS authentication manager
            feedback: interrupts the running request when canceled
        """
        self.authcfg = authcfg
        self.feedback = feedback

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
            method: HTTP method: GET, POST, PUT or DELETE
            url: URL, without its query string
            params: query string. A sequence repeats the parameter.
            headers: request headers
            data: body
            timeout: seconds to wait for the server. QGIS's own network timeout setting
                still applies when it is shorter.

        Raises:
            ValueError: if the method is not supported
            HttpTransportError: if no response was received

        Returns:
            response, whatever its status code
        """
        from qgis.core import QgsBlockingNetworkRequest
        from qgis.PyQt.QtCore import QUrl, QUrlQuery
        from qgis.PyQt.QtNetwork import QNetworkRequest

        target = QUrl(url)
        if params:
            query = QUrlQuery()
            for name, values in params.items():
                for value in [values] if isinstance(values, str) else values:
                    encoded = bytes(QUrl.toPercentEncoding(value)).decode("ascii")
                    query.addQueryItem(name, encoded)
            target.setQuery(query)

        network_request = QNetworkRequest(target)
        for name, value in (headers or {}).items():
            network_request.setRawHeader(
                name.encode("latin-1"), value.encode("latin-1")
            )
        if timeout is not None:
            network_request.setTransferTimeout(int(timeout * 1000))
        # the cookie jar of QGIS, shared with everything else running in QGIS, would
        # override the Cookie header given by the caller: see HttpClient
        for attribute in (
            QNetworkRequest.Attribute.CookieLoadControlAttribute,
            QNetworkRequest.Attribute.CookieSaveControlAttribute,
        ):
            network_request.setAttribute(attribute, QNetworkRequest.LoadControl.Manual)

        blocking_request = QgsBlockingNetworkRequest()
        if self.authcfg:
            blocking_request.setAuthCfg(self.authcfg)

        body = data or b""
        if method == "GET":
            # a catalog record may have changed since the last time: no cache
            blocking_request.get(network_request, True, self.feedback)
        elif method == "POST":
            blocking_request.post(network_request, body, True, self.feedback)
        elif method == "PUT":
            blocking_request.put(network_request, body, self.feedback)
        elif method == "DELETE":
            blocking_request.deleteResource(network_request, self.feedback)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}.")

        reply = blocking_request.reply()
        status_code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        # an HTTP error is an error for QGIS too, but it got a response
        if status_code is None:
            raise HttpTransportError(
                f"{method} {url} failed: {blocking_request.errorMessage()}"
            )

        response_headers = {
            bytes(name).decode("latin-1").lower(): bytes(
                reply.rawHeader(bytes(name))
            ).decode("latin-1")
            for name in reply.rawHeaderList()
        }
        return HttpResponse(
            status_code=int(status_code),
            headers=response_headers,
            cookies=parse_set_cookie(response_headers.get("set-cookie", "")),
            content=bytes(reply.content()),
            url=target.toString(),
        )
