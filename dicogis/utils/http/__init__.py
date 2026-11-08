#! python3  # noqa: E265

"""HTTP clients: requests or the network stack of QGIS, behind a common contract.

The backend is picked from the `DICOGIS_HTTP_BACKEND` environment variable, on the same
model as `DICOGIS_QT_API`:

- `auto` (default): the network stack of QGIS when running inside QGIS, i.e. a
  `QgsApplication` is running, requests otherwise.
- `requests`: always requests.
- `qgis`: always the network stack of QGIS.
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# Standard library
from __future__ import annotations

from os import getenv
from typing import TYPE_CHECKING

# project
from dicogis.utils.http.client import (
    HttpClient,
    HttpError,
    HttpResponse,
    HttpStatusError,
    HttpTransportError,
    parse_set_cookie,
)
from dicogis.utils.qgis_runtime import qgis_application_is_running


if TYPE_CHECKING:
    from qgis.core import QgsFeedback


# ##############################################################################
# ########## Globals ###############
# ##################################

__all__ = [
    "HTTP_BACKENDS",
    "HTTP_BACKEND_ENV_VAR",
    "HttpClient",
    "HttpError",
    "HttpResponse",
    "HttpStatusError",
    "HttpTransportError",
    "get_http_client",
    "parse_set_cookie",
    "resolve_http_backend",
]

HTTP_BACKEND_ENV_VAR: str = "DICOGIS_HTTP_BACKEND"
HTTP_BACKENDS: tuple[str, ...] = ("auto", "requests", "qgis")

# ##############################################################################
# ########## Functions #############
# ##################################


def resolve_http_backend(requested: str | None = None) -> str:
    """Determine which HTTP backend to use.

    Args:
        requested: one of `HTTP_BACKENDS`, case-insensitive. Defaults to the value of
            the `DICOGIS_HTTP_BACKEND` environment variable, or `auto` if unset.

    Raises:
        ValueError: if the requested backend is unknown

    Returns:
        the backend to use: `requests` or `qgis`
    """
    if requested is None:
        requested = getenv(HTTP_BACKEND_ENV_VAR) or "auto"
    requested = requested.strip().lower()

    if requested not in HTTP_BACKENDS:
        raise ValueError(
            f"Invalid {HTTP_BACKEND_ENV_VAR} value: '{requested}'. "
            f"Expected one of: {', '.join(HTTP_BACKENDS)}."
        )

    if requested == "auto":
        return "qgis" if qgis_application_is_running() else "requests"
    return requested


def get_http_client(
    backend: str | None = None,
    *,
    authcfg: str | None = None,
    feedback: QgsFeedback | None = None,
) -> HttpClient:
    """Build the HTTP client of the running environment.

    Args:
        backend: see `resolve_http_backend()`
        authcfg: identifier of a configuration of the QGIS authentication manager
        feedback: interrupts the running request when canceled (QGIS backend)

    Raises:
        ValueError: if the backend is unknown, or authcfg is given while QGIS isn't used

    Returns:
        HTTP client
    """
    resolved_backend = resolve_http_backend(backend)

    if resolved_backend == "qgis":
        from dicogis.utils.http.backend_qgis import QgisHttpClient

        return QgisHttpClient(authcfg=authcfg, feedback=feedback)

    if authcfg:
        raise ValueError(
            "An authentication configuration (authcfg) only exists within QGIS."
        )
    from dicogis.utils.http.backend_requests import RequestsHttpClient

    return RequestsHttpClient()
