#! python3  # noqa: E265

"""In-memory implementation of dicogis.utils.http.HttpClient, for the publishers' tests."""

# ##############################################################################
# ########## Libraries #############
# ##################################

# standard library
import json
from dataclasses import dataclass

# project
from dicogis.utils.http import HttpResponse, HttpTransportError


# ##############################################################################
# ########## Classes ###############
# ##################################


@dataclass
class RecordedCall:
    """A request received by the fake client."""

    method: str
    url: str
    params: dict | None
    headers: dict
    data: bytes | None
    timeout: float | None


class FakeHttpClient:
    """Answers from a list of canned responses and records the requests.

    Responses of a route are served in order, the last one being repeated. A request
    without a route is answered with a 404.
    """

    def __init__(self) -> None:
        """Start with no route."""
        self.routes: dict[tuple[str, str], list[HttpResponse | Exception]] = {}
        self.calls: list[RecordedCall] = []

    def add(
        self,
        method: str,
        url: str,
        status_code: int = 200,
        *,
        content: bytes = b"",
        json_body: object = None,
        cookies: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        """Add a response to a route.

        Args:
            method: HTTP method of the route
            url: URL of the route, without its query string
            status_code: status code to answer with
            content: body to answer with
            json_body: object to answer with as JSON, instead of content
            cookies: cookies to set
            headers: response headers
        """
        if json_body is not None:
            content = json.dumps(json_body).encode("UTF-8")
        self.routes.setdefault((method, url), []).append(
            HttpResponse(
                status_code=status_code,
                headers=headers or {},
                cookies=cookies or {},
                content=content,
                url=url,
            )
        )

    def add_transport_error(self, method: str, url: str, message: str = "boom") -> None:
        """Make a route fail without an HTTP response.

        Args:
            method: HTTP method of the route
            url: URL of the route, without its query string
            message: error message
        """
        self.routes.setdefault((method, url), []).append(HttpTransportError(message))

    def request(
        self,
        method: str,
        url: str,
        *,
        params=None,
        headers=None,
        data=None,
        timeout=None,
    ) -> HttpResponse:
        """Record the request and serve the next response of its route.

        Returns:
            canned response

        Raises:
            HttpTransportError: if the route was told to fail
        """
        self.calls.append(
            RecordedCall(
                method=method,
                url=url,
                params=dict(params) if params else None,
                headers=dict(headers) if headers else {},
                data=data,
                timeout=timeout,
            )
        )
        responses = self.routes.get((method, url))
        if not responses:
            return HttpResponse(status_code=404, url=url)
        response = responses.pop(0) if len(responses) > 1 else responses[0]
        if isinstance(response, Exception):
            raise response
        return response

    def calls_to(self, method: str, url: str | None = None) -> list[RecordedCall]:
        """List the requests received by a route.

        Args:
            method: HTTP method
            url: URL. Defaults to any.

        Returns:
            recorded calls, in order
        """
        return [
            call
            for call in self.calls
            if call.method == method and (url is None or call.url == url)
        ]
