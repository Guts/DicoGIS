#! python3  # noqa: E265

"""HTTP clients: requests or the network stack of QGIS, behind a common contract."""

# ##############################################################################
# ########## Libraries #############
# ##################################

# project
from dicogis.utils.http.client import (
    HttpClient,
    HttpError,
    HttpResponse,
    HttpStatusError,
    HttpTransportError,
    parse_set_cookie,
)


# ##############################################################################
# ########## Globals ###############
# ##################################

__all__ = [
    "HttpClient",
    "HttpError",
    "HttpResponse",
    "HttpStatusError",
    "HttpTransportError",
    "parse_set_cookie",
]
