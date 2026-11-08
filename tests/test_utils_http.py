#! python3  # noqa: E265

"""
Tests for the HTTP clients and the selection of their backend.

The QGIS backend is exercised with a fake qgis package around the real PyQt6 network
classes: it checks how requests are built, not QGIS itself, which no test runs.

Usage from the repo root folder:
    pytest tests/test_utils_http.py
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# standard library
import sys
import types

# 3rd party
import pytest
import responses
from responses import matchers

# project
from dicogis.utils.http import (
    HTTP_BACKEND_ENV_VAR,
    HttpClient,
    HttpResponse,
    HttpStatusError,
    HttpTransportError,
    get_http_client,
    parse_set_cookie,
    resolve_http_backend,
)
from dicogis.utils.http.backend_qgis import QgisHttpClient
from dicogis.utils.http.backend_requests import RequestsHttpClient
from tests.fixtures.fake_http_client import FakeHttpClient


# ##############################################################################
# ########## Globals ###############
# ##################################

URL = "https://catalog.example/api"

# ##############################################################################
# ########## Fixtures ##############
# ##################################


@pytest.fixture
def no_backend_env(monkeypatch) -> None:
    monkeypatch.delenv(HTTP_BACKEND_ENV_VAR, raising=False)


def _fake_qgis_core(monkeypatch, *, running: bool) -> None:
    """Pretend a `qgis.core` is loaded, with a running QgsApplication or not."""

    class QgsApplication:
        current = None

        @classmethod
        def instance(cls):
            return cls.current

    if running:
        QgsApplication.current = QgsApplication()
    fake_core = types.ModuleType("qgis.core")
    fake_core.QgsApplication = QgsApplication
    monkeypatch.setitem(sys.modules, "qgis.core", fake_core)


class _FakeReply:
    def __init__(self, status_code, headers, content):
        self.status_code = status_code
        self.headers = headers
        self._content = content

    def attribute(self, _attribute):
        return self.status_code

    def rawHeaderList(self):
        return list(self.headers)

    def rawHeader(self, name):
        return self.headers[bytes(name)]

    def content(self):
        return self._content


class _FakeBlockingRequest:
    """Stands in for QgsBlockingNetworkRequest and records how it is used."""

    last = None
    next_reply = _FakeReply(200, {}, b"")

    def __init__(self):
        type(self).last = self
        self.authcfg = None
        self.call = None

    def setAuthCfg(self, authcfg):
        self.authcfg = authcfg

    def get(self, request, force_refresh, feedback):
        self.call = ("GET", request, None, force_refresh, feedback)

    def post(self, request, data, force_refresh, feedback):
        self.call = ("POST", request, data, force_refresh, feedback)

    def put(self, request, data, feedback):
        self.call = ("PUT", request, data, None, feedback)

    def deleteResource(self, request, feedback):
        self.call = ("DELETE", request, None, None, feedback)

    def reply(self):
        return self.next_reply

    def errorMessage(self):
        return "connection refused"


@pytest.fixture
def fake_qgis(monkeypatch):
    """Provide the qgis modules the QGIS backend needs, around the real PyQt6."""
    pytest.importorskip("PyQt6.QtNetwork", reason="PyQt6 (gui extra) required")
    from PyQt6 import QtCore, QtNetwork

    fake_core = types.ModuleType("qgis.core")
    fake_core.QgsBlockingNetworkRequest = _FakeBlockingRequest
    fake_pyqt = types.ModuleType("qgis.PyQt")
    monkeypatch.setitem(sys.modules, "qgis", types.ModuleType("qgis"))
    monkeypatch.setitem(sys.modules, "qgis.core", fake_core)
    monkeypatch.setitem(sys.modules, "qgis.PyQt", fake_pyqt)
    monkeypatch.setitem(sys.modules, "qgis.PyQt.QtCore", QtCore)
    monkeypatch.setitem(sys.modules, "qgis.PyQt.QtNetwork", QtNetwork)
    monkeypatch.setattr(
        _FakeBlockingRequest, "next_reply", _FakeReply(200, {}, b""), raising=True
    )
    return QtNetwork


# ##############################################################################
# ########## Selection tests #######
# ##################################


@pytest.mark.usefixtures("no_backend_env")
def test_auto_is_requests_outside_qgis():
    assert resolve_http_backend() == "requests"


@pytest.mark.usefixtures("no_backend_env")
def test_auto_is_requests_when_qgis_is_only_imported(monkeypatch):
    _fake_qgis_core(monkeypatch, running=False)

    assert resolve_http_backend() == "requests"


@pytest.mark.usefixtures("no_backend_env")
def test_auto_is_qgis_when_a_qgs_application_is_running(monkeypatch):
    _fake_qgis_core(monkeypatch, running=True)

    assert resolve_http_backend() == "qgis"


@pytest.mark.parametrize(
    ("value", "expected"),
    [("requests", "requests"), ("qgis", "qgis"), (" QGIS ", "qgis")],
)
def test_environment_variable_forces_the_backend(monkeypatch, value, expected):
    monkeypatch.setenv(HTTP_BACKEND_ENV_VAR, value)

    assert resolve_http_backend() == expected


def test_environment_variable_wins_over_a_running_qgis(monkeypatch):
    _fake_qgis_core(monkeypatch, running=True)
    monkeypatch.setenv(HTTP_BACKEND_ENV_VAR, "requests")

    assert resolve_http_backend() == "requests"


def test_unknown_backend_is_refused(monkeypatch):
    monkeypatch.setenv(HTTP_BACKEND_ENV_VAR, "curl")

    with pytest.raises(ValueError, match=HTTP_BACKEND_ENV_VAR):
        resolve_http_backend()


@pytest.mark.parametrize(
    ("backend", "expected"),
    [("requests", RequestsHttpClient), ("qgis", QgisHttpClient)],
)
def test_client_of_the_backend(backend, expected):
    assert isinstance(get_http_client(backend), expected)


def test_authcfg_needs_qgis():
    with pytest.raises(ValueError, match="authcfg"):
        get_http_client("requests", authcfg="abc1234")


def test_authcfg_is_given_to_the_qgis_client():
    assert get_http_client("qgis", authcfg="abc1234").authcfg == "abc1234"


@pytest.mark.parametrize(
    "client", [RequestsHttpClient(), QgisHttpClient(), FakeHttpClient()]
)
def test_clients_follow_the_protocol(client):
    assert isinstance(client, HttpClient)


def test_importing_the_package_loads_neither_requests_backend_nor_qgis():
    """dicogis.utils.http is imported by the publication code, also in QGIS."""
    import subprocess

    code = (
        "import sys; import dicogis.utils.http; "
        "print('qgis' in sys.modules, "
        "'dicogis.utils.http.backend_requests' in sys.modules)"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )

    assert result.stdout.strip() == "False False"


# ##############################################################################
# ########## Response tests ########
# ##################################


def test_raise_for_status():
    HttpResponse(status_code=204).raise_for_status()
    HttpResponse(status_code=302).raise_for_status()

    with pytest.raises(HttpStatusError, match="404") as error:
        HttpResponse(status_code=404, url=URL).raise_for_status()

    assert error.value.response.status_code == 404
    assert URL in str(error.value)


def test_response_body():
    response = HttpResponse(status_code=200, content='{"é": 1}'.encode())

    assert response.json() == {"é": 1}
    assert response.text == '{"é": 1}'


def test_parse_set_cookie():
    assert parse_set_cookie("") == {}
    assert parse_set_cookie("XSRF-TOKEN=abc; Path=/; HttpOnly") == {"XSRF-TOKEN": "abc"}
    assert parse_set_cookie("a=1; Path=/\nb=2=3; Secure") == {"a": "1", "b": "2=3"}
    assert parse_set_cookie("no_value") == {}


# ##############################################################################
# ########## requests backend tests #
# ##################################


@responses.activate
def test_requests_backend_request():
    responses.put(
        URL,
        body=b"created",
        status=201,
        headers={"X-Custom": "yes", "Set-Cookie": "XSRF-TOKEN=abc; Path=/"},
        match=[
            matchers.query_param_matcher({"a": "1", "b": ["2", "3"]}),
            matchers.header_matcher({"X-Sent": "sent"}),
            matchers.request_kwargs_matcher({"timeout": 5.0}),
        ],
    )

    response = RequestsHttpClient().request(
        "PUT",
        URL,
        params={"a": "1", "b": ["2", "3"]},
        headers={"X-Sent": "sent"},
        data=b"body",
        timeout=5.0,
    )

    assert responses.calls[0].request.body == b"body"
    assert response.status_code == 201
    assert response.content == b"created"
    assert response.headers["x-custom"] == "yes"
    assert response.cookies == {"XSRF-TOKEN": "abc"}


@responses.activate
def test_requests_backend_returns_http_errors():
    responses.get(URL, status=500)

    assert RequestsHttpClient().request("GET", URL).status_code == 500


@responses.activate
def test_requests_backend_raises_transport_errors():
    with pytest.raises(HttpTransportError, match="failed"):
        RequestsHttpClient().request("GET", URL)


@responses.activate
def test_requests_backend_stores_no_cookie():
    """The session's jar would otherwise override the Cookie header of the caller."""
    responses.get(URL, headers={"Set-Cookie": "XSRF-TOKEN=from-server; Path=/"})
    client = RequestsHttpClient()

    first = client.request("GET", URL)
    client.request("GET", URL, headers={"Cookie": "XSRF-TOKEN=from-caller"})

    assert first.cookies == {"XSRF-TOKEN": "from-server"}
    assert responses.calls[1].request.headers["Cookie"] == "XSRF-TOKEN=from-caller"


# ##############################################################################
# ########## QGIS backend tests ####
# ##################################


@pytest.mark.usefixtures("fake_qgis")
def test_qgis_backend_builds_the_request():
    feedback = object()

    QgisHttpClient(authcfg="abc1234", feedback=feedback).request(
        "PUT",
        URL,
        params={"a": "x y", "b": ["2", "3"]},
        headers={"X-Sent": "sent"},
        data=b"body",
        timeout=2.5,
    )

    blocking_request = _FakeBlockingRequest.last
    method, request, data, _force_refresh, sent_feedback = blocking_request.call
    assert method == "PUT"
    assert data == b"body"
    assert sent_feedback is feedback
    assert blocking_request.authcfg == "abc1234"
    assert request.url().toString(
        request.url().ComponentFormattingOption.FullyEncoded
    ) == (f"{URL}?a=x%20y&b=2&b=3")
    assert bytes(request.rawHeader(b"X-Sent")) == b"sent"
    assert request.transferTimeout() == 2500


def test_qgis_backend_leaves_the_cookie_jar_out(fake_qgis):
    attributes = fake_qgis.QNetworkRequest.Attribute

    QgisHttpClient().request("GET", URL, headers={"Cookie": "XSRF-TOKEN=from-caller"})

    _method, request, *_ = _FakeBlockingRequest.last.call
    for attribute in (
        attributes.CookieLoadControlAttribute,
        attributes.CookieSaveControlAttribute,
    ):
        assert (
            request.attribute(attribute) == fake_qgis.QNetworkRequest.LoadControl.Manual
        )
    assert bytes(request.rawHeader(b"Cookie")) == b"XSRF-TOKEN=from-caller"


@pytest.mark.parametrize(
    ("method", "expected_data", "expected_refresh"),
    [
        ("GET", None, True),
        ("POST", b"body", True),
        ("PUT", b"body", None),
        ("DELETE", None, None),
    ],
)
@pytest.mark.usefixtures("fake_qgis")
def test_qgis_backend_methods(method, expected_data, expected_refresh):
    QgisHttpClient().request(method, URL, data=b"body")

    sent_method, _request, data, force_refresh, _ = _FakeBlockingRequest.last.call
    assert (sent_method, data, force_refresh) == (
        method,
        expected_data,
        expected_refresh,
    )


@pytest.mark.usefixtures("fake_qgis")
def test_qgis_backend_refuses_other_methods():
    with pytest.raises(ValueError, match="PATCH"):
        QgisHttpClient().request("PATCH", URL)


def test_qgis_backend_reads_the_response(fake_qgis, monkeypatch):
    monkeypatch.setattr(
        _FakeBlockingRequest,
        "next_reply",
        _FakeReply(
            403,
            {b"Set-Cookie": b"a=1; Path=/\nb=2", b"X-Custom": b"yes"},
            b"denied",
        ),
    )

    response = QgisHttpClient().request("GET", URL)

    assert response.status_code == 403
    assert response.content == b"denied"
    assert response.headers["x-custom"] == "yes"
    assert response.cookies == {"a": "1", "b": "2"}


def test_qgis_backend_raises_transport_errors(fake_qgis, monkeypatch):
    monkeypatch.setattr(_FakeBlockingRequest, "next_reply", _FakeReply(None, {}, b""))

    with pytest.raises(HttpTransportError, match="connection refused"):
        QgisHttpClient().request("GET", URL)


# ##############################################################################
# ########## Fake client tests #####
# ##################################


def test_fake_client_serves_routes_in_order_and_records_calls():
    client = FakeHttpClient()
    client.add("GET", URL, 200, content=b"first")
    client.add("GET", URL, 500)

    assert client.request("GET", URL, params={"a": "1"}).content == b"first"
    assert client.request("GET", URL).status_code == 500
    assert client.request("GET", URL).status_code == 500
    assert client.request("GET", f"{URL}/other").status_code == 404
    assert client.calls_to("GET", URL)[0].params == {"a": "1"}
    assert len(client.calls_to("GET")) == 4


def test_fake_client_transport_error():
    client = FakeHttpClient()
    client.add_transport_error("GET", URL)

    with pytest.raises(HttpTransportError):
        client.request("GET", URL)


# ##############################################################################
# ##### Stand alone program ########
# ##################################
if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
