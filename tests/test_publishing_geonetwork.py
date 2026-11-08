#! python3  # noqa: E265

"""
Tests for the GeoNetwork publication core, against an in-memory HTTP client.

Checks what's sent to the catalog: a real GeoNetwork runs in the integration workflow.

Usage from the repo root folder:
    pytest tests/test_publishing_geonetwork.py
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# standard library
import base64
import sys
from datetime import date
from pathlib import Path

# 3rd party
import pytest
from lxml import etree

# project
from dicogis.export.catalog_record import CatalogRecord
from dicogis.export.to_iso19139 import ISO19139_NAMESPACES, record_to_iso19139
from dicogis.publishing.geonetwork import (
    GeonetworkAuthenticationError,
    GeonetworkCredentials,
    publish_metadata_folder,
)
from dicogis.utils.http import HttpTransportError
from tests.fixtures.fake_http_client import FakeHttpClient


# ##############################################################################
# ########## Globals ###############
# ##################################

URL_BASE = "https://catalogue.example/geonetwork"
ME_URL = f"{URL_BASE}/srv/api/me"
RECORDS_URL = f"{URL_BASE}/srv/api/records"
IDENTIFIER = "6a4e5ba7-e7dd-533a-a57c-42632717ecfe"
FORMATTER_URL = f"{RECORDS_URL}/{IDENTIFIER}/formatters/xml"
CREDENTIALS = GeonetworkCredentials(username="editor", password="s3cret")
IDENT = "gmd:identificationInfo/gmd:MD_DataIdentification"
TITLE_PATH = f"{IDENT}/gmd:citation/gmd:CI_Citation/gmd:title/gco:CharacterString"
ABSTRACT_PATH = f"{IDENT}/gmd:abstract/gco:CharacterString"

# ##############################################################################
# ########## Classes ###############
# ##################################


class _RecordingReporter:
    """ProgressReporter recording what it's told, asking to stop after some files."""

    def __init__(self, cancel_after: int | None = None) -> None:
        self.cancel_after = cancel_after
        self.total = None
        self.count = 0

    def set_message(self, message: str) -> None:
        pass

    def increment(self, amount: int = 1) -> None:
        self.count += amount

    def set_total(self, total: int) -> None:
        self.total = total

    def is_canceled(self) -> bool:
        return self.cancel_after is not None and self.count >= self.cancel_after


# ##############################################################################
# ########## Functions #############
# ##################################


def _record_xml(identifier: str = IDENTIFIER, **overrides) -> bytes:
    values = dict(
        identifier=identifier,
        title="local title",
        abstract="local abstract",
        language="fre",
        metadata_date=date(2026, 11, 8),
        spatial_representation="vector",
    )
    values.update(overrides)
    return etree.tostring(record_to_iso19139(CatalogRecord(**values)))


def _write_record(folder: Path, filename: str = "a.xml", **overrides) -> Path:
    path = folder / filename
    path.write_bytes(_record_xml(**overrides))
    return path


def _client(*, me_status: int = 200, cookies: dict | None = None) -> FakeHttpClient:
    client = FakeHttpClient()
    client.add(
        "GET",
        ME_URL,
        me_status,
        json_body={"username": "editor"},
        cookies={"XSRF-TOKEN": "token-1"} if cookies is None else cookies,
    )
    client.add("PUT", RECORDS_URL, 201, json_body={"numberOfRecordsWithErrors": 0})
    return client


def _publish(folder: Path, client: FakeHttpClient, **overrides):
    kwargs = dict(
        input_folder=folder,
        url_base=URL_BASE,
        group="2",
        credentials=CREDENTIALS,
        http_client=client,
        timeout=7.0,
    )
    kwargs.update(overrides)
    return publish_metadata_folder(**kwargs)


def _sent(client: FakeHttpClient, index: int = 0) -> etree._Element:
    return etree.fromstring(client.calls_to("PUT", RECORDS_URL)[index].data)


def _text(root: etree._Element, xpath: str) -> str | None:
    return root.findtext(xpath, namespaces=ISO19139_NAMESPACES)


# ##############################################################################
# ########## Session tests #########
# ##################################


def test_session_checks_the_account_with_basic_authentication(tmp_path):
    _write_record(tmp_path)
    client = _client()

    _publish(tmp_path, client)

    me_call = client.calls_to("GET", ME_URL)[0]
    expected = base64.b64encode(b"editor:s3cret").decode()
    assert me_call.headers["Authorization"] == f"Basic {expected}"
    assert me_call.timeout == 7.0


def test_writes_send_the_token_as_cookie_and_header(tmp_path):
    _write_record(tmp_path)
    client = _client(cookies={"XSRF-TOKEN": "token-1", "JSESSIONID": "s"})

    _publish(tmp_path, client)

    headers = client.calls_to("PUT", RECORDS_URL)[0].headers
    assert headers["X-XSRF-TOKEN"] == "token-1"
    assert "XSRF-TOKEN=token-1" in headers["Cookie"]
    assert "JSESSIONID=s" in headers["Cookie"]
    assert headers["Authorization"].startswith("Basic ")
    assert headers["Content-Type"] == "application/xml"


def test_a_renewed_token_is_used_afterwards(tmp_path):
    _write_record(tmp_path, "a.xml", identifier="a")
    _write_record(tmp_path, "b.xml", identifier="b")
    client = FakeHttpClient()
    client.add("GET", ME_URL, 200, json_body={}, cookies={"XSRF-TOKEN": "token-1"})
    client.add("PUT", RECORDS_URL, 201, cookies={"XSRF-TOKEN": "token-2"})
    client.add("PUT", RECORDS_URL, 201)

    _publish(tmp_path, client)

    puts = client.calls_to("PUT", RECORDS_URL)
    assert puts[0].headers["X-XSRF-TOKEN"] == "token-1"
    assert puts[1].headers["X-XSRF-TOKEN"] == "token-2"


def test_no_credentials_means_no_basic_authentication(tmp_path):
    """Within QGIS, an authentication configuration handles it."""
    _write_record(tmp_path)
    client = _client()

    _publish(tmp_path, client, credentials=None)

    assert "Authorization" not in client.calls_to("GET", ME_URL)[0].headers
    assert "Authorization" not in client.calls_to("PUT", RECORDS_URL)[0].headers


@pytest.mark.parametrize(
    ("status", "message"),
    [(204, "anonymous"), (401, "401"), (404, "404"), (500, "500")],
)
def test_failed_login_stops_everything(tmp_path, status, message):
    _write_record(tmp_path)
    client = _client(me_status=status)

    with pytest.raises(GeonetworkAuthenticationError, match=message):
        _publish(tmp_path, client)

    assert not client.calls_to("PUT")


def test_no_token_stops_everything(tmp_path):
    _write_record(tmp_path)
    client = _client(cookies={})

    with pytest.raises(GeonetworkAuthenticationError, match="XSRF-TOKEN"):
        _publish(tmp_path, client)

    assert not client.calls_to("PUT")


def test_unreachable_catalog_stops_everything(tmp_path):
    _write_record(tmp_path)
    client = FakeHttpClient()
    client.add_transport_error("GET", ME_URL)

    with pytest.raises(HttpTransportError):
        _publish(tmp_path, client)


def test_credentials_keep_the_password_out_of_their_representation():
    assert "s3cret" not in repr(CREDENTIALS)
    assert "s3cret" not in str(CREDENTIALS)


def test_portal_and_trailing_slash_of_the_url(tmp_path):
    _write_record(tmp_path)
    client = FakeHttpClient()
    client.add(
        "GET",
        f"{URL_BASE}/inspire/api/me",
        200,
        json_body={},
        cookies={"XSRF-TOKEN": "t"},
    )
    client.add("PUT", f"{URL_BASE}/inspire/api/records", 201)

    report = _publish(tmp_path, client, url_base=f"{URL_BASE}/", portal="inspire")

    assert report.published == 1


# ##############################################################################
# ########## Parameters tests ######
# ##################################


def test_no_xml_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        _publish(tmp_path, _client())


def test_no_url(tmp_path):
    _write_record(tmp_path)

    with pytest.raises(ValueError, match="URL"):
        _publish(tmp_path, _client(), url_base="")


@pytest.mark.parametrize("group", ["", "  ", "editors", None])
def test_group_must_be_an_identifier(tmp_path, group):
    """GeoNetwork 4.4 parses it as a number before anything else."""
    _write_record(tmp_path)
    client = _client()

    with pytest.raises(ValueError, match="group"):
        _publish(tmp_path, client, group=group)

    assert not client.calls


def test_unknown_update_mode(tmp_path):
    _write_record(tmp_path)

    with pytest.raises(ValueError, match="merge"):
        _publish(tmp_path, _client(), update_mode="merge")


# ##############################################################################
# ########## Overwrite tests #######
# ##################################


def test_overwrite_sends_the_file_as_is(tmp_path):
    path = _write_record(tmp_path)
    client = _client()

    report = _publish(tmp_path, client)

    call = client.calls_to("PUT", RECORDS_URL)[0]
    assert call.data == path.read_bytes()
    assert call.timeout == 7.0
    assert call.params == {
        "metadataType": "METADATA",
        "uuidProcessing": "OVERWRITE",
        "group": "2",
        "publishToAll": "false",
        "rejectIfInvalid": "false",
    }
    assert (report.published, report.ignored, report.failed) == (1, 0, 0)


def test_overwrite_options_are_sent(tmp_path):
    _write_record(tmp_path)
    client = _client()

    _publish(
        tmp_path,
        client,
        group=" 12 ",
        categories=["1", "3"],
        publish_to_all=True,
        reject_if_invalid=True,
    )

    params = client.calls_to("PUT", RECORDS_URL)[0].params
    assert params["group"] == "12"
    assert params["category"] == ["1", "3"]
    assert params["publishToAll"] == "true"
    assert params["rejectIfInvalid"] == "true"


def test_overwrite_does_not_read_the_catalog(tmp_path):
    _write_record(tmp_path)
    client = _client()

    _publish(tmp_path, client)

    assert not client.calls_to("GET", FORMATTER_URL)


def test_other_xml_files_are_ignored(tmp_path):
    _write_record(tmp_path)
    (tmp_path / "other.xml").write_text("<root/>", encoding="UTF-8")
    (tmp_path / "19115-3.xml").write_text(
        '<mdb:MD_Metadata xmlns:mdb="http://standards.iso.org/iso/19115/-3/mdb/2.0"/>',
        encoding="UTF-8",
    )
    client = _client()

    report = _publish(tmp_path, client)

    assert (report.published, report.ignored, report.failed) == (1, 2, 0)
    assert len(client.calls_to("PUT")) == 1


def test_broken_xml_file_fails_alone(tmp_path):
    _write_record(tmp_path)
    (tmp_path / "broken.xml").write_text("<not closed", encoding="UTF-8")

    report = _publish(tmp_path, _client())

    assert (report.published, report.failed) == (1, 1)
    assert "broken.xml" in report.errors[0]


def test_record_without_identifier_fails(tmp_path):
    (tmp_path / "a.xml").write_text(
        '<gmd:MD_Metadata xmlns:gmd="http://www.isotc211.org/2005/gmd"/>',
        encoding="UTF-8",
    )
    client = _client()

    report = _publish(tmp_path, client)

    assert report.failed == 1
    assert "fileIdentifier" in report.errors[0]
    assert not client.calls_to("PUT")


def test_entities_of_a_file_are_not_resolved(tmp_path):
    secret_file = tmp_path / "secret.txt"
    secret_file.write_text("my secret", encoding="UTF-8")
    (tmp_path / "evil.xml").write_text(
        f"""<!DOCTYPE foo [<!ENTITY xxe SYSTEM "{secret_file.as_uri()}">]>
        <gmd:MD_Metadata xmlns:gmd="http://www.isotc211.org/2005/gmd"
                         xmlns:gco="http://www.isotc211.org/2005/gco">
            <gmd:fileIdentifier><gco:CharacterString>&xxe;</gco:CharacterString></gmd:fileIdentifier>
        </gmd:MD_Metadata>""",
        encoding="UTF-8",
    )
    client = _client()

    _publish(tmp_path, client)

    assert not any(call.data and b"my secret" in call.data for call in client.calls)


def test_http_error_fails_alone_and_tells_what_the_catalog_said(tmp_path):
    _write_record(tmp_path, "a.xml", identifier="a")
    _write_record(tmp_path, "b.xml", identifier="b")
    client = FakeHttpClient()
    client.add("GET", ME_URL, 200, json_body={}, cookies={"XSRF-TOKEN": "t"})
    client.add("PUT", RECORDS_URL, 400, content=b'{"message": "XSD validation failed"}')
    client.add("PUT", RECORDS_URL, 201)

    report = _publish(tmp_path, client)

    assert (report.published, report.failed) == (1, 1)
    assert "HTTP 400" in report.errors[0]
    assert "XSD validation failed" in report.errors[0]


def test_transport_error_fails_alone(tmp_path):
    _write_record(tmp_path)
    client = FakeHttpClient()
    client.add("GET", ME_URL, 200, json_body={}, cookies={"XSRF-TOKEN": "t"})
    client.add_transport_error("PUT", RECORDS_URL, "timed out")

    report = _publish(tmp_path, client)

    assert report.failed == 1
    assert "timed out" in report.errors[0]


def test_errors_in_a_successful_response_count_as_failures(tmp_path):
    _write_record(tmp_path)
    client = FakeHttpClient()
    client.add("GET", ME_URL, 200, json_body={}, cookies={"XSRF-TOKEN": "t"})
    client.add(
        "PUT",
        RECORDS_URL,
        201,
        json_body={"numberOfRecordsWithErrors": 1, "errors": []},
    )

    report = _publish(tmp_path, client)

    assert report.failed == 1
    assert "numberOfRecordsWithErrors" in report.errors[0]


def test_progress_and_cancellation(tmp_path):
    for name in ("a", "b", "c"):
        _write_record(tmp_path, f"{name}.xml", identifier=name)
    client = _client()
    reporter = _RecordingReporter(cancel_after=2)

    report = _publish(tmp_path, client, progress_reporter=reporter)

    assert reporter.total == 3
    assert report.canceled is True
    assert report.published == 2
    assert len(client.calls_to("PUT")) == 2


# ##############################################################################
# ########## Complete mode tests ###
# ##################################


def test_complete_inserts_a_record_the_catalog_does_not_have(tmp_path):
    path = _write_record(tmp_path)
    client = _client()
    client.add("GET", FORMATTER_URL, 404)

    report = _publish(tmp_path, client, update_mode="complete")

    assert client.calls_to("PUT", RECORDS_URL)[0].data == path.read_bytes()
    assert report.published == 1
    assert report.added_fields == {}


def test_complete_reads_the_working_copy_without_raising_popularity(tmp_path):
    _write_record(tmp_path)
    client = _client()
    client.add("GET", FORMATTER_URL, 404)

    _publish(tmp_path, client, update_mode="complete")

    assert client.calls_to("GET", FORMATTER_URL)[0].params == {
        "approved": "false",
        "increasePopularity": "false",
    }


def test_complete_fills_what_is_empty_and_leaves_the_rest(tmp_path):
    _write_record(tmp_path)
    client = _client()
    remote = _record_xml(title="title edited by hand", abstract="to remove").replace(
        b"to remove", b""
    )
    client.add("GET", FORMATTER_URL, 200, content=remote)

    report = _publish(tmp_path, client, update_mode="complete")

    sent = _sent(client)
    assert _text(sent, TITLE_PATH) == "title edited by hand"
    assert _text(sent, ABSTRACT_PATH) == "local abstract"
    assert (
        client.calls_to("PUT", RECORDS_URL)[0].params["uuidProcessing"] == "OVERWRITE"
    )
    assert report.published == 1
    assert report.added_fields == {"a.xml": ["abstract"]}


def test_complete_sends_nothing_when_nothing_is_missing(tmp_path):
    _write_record(tmp_path)
    client = _client()
    client.add("GET", FORMATTER_URL, 200, content=_record_xml(title="edited"))

    report = _publish(tmp_path, client, update_mode="complete")

    assert not client.calls_to("PUT")
    assert report.up_to_date == 1
    assert report.published == 0
    assert report.total == 1


def test_complete_leaves_a_record_of_another_schema_as_is(tmp_path):
    _write_record(tmp_path)
    client = _client()
    client.add(
        "GET",
        FORMATTER_URL,
        200,
        content=(
            b'<mdb:MD_Metadata xmlns:mdb="http://standards.iso.org/iso/19115/-3/mdb/2.0"/>'
        ),
    )

    report = _publish(tmp_path, client, update_mode="complete")

    assert not client.calls_to("PUT")
    assert report.ignored == 1
    assert "isn't an ISO 19139" in report.errors[0]


def test_complete_read_refused_fails_alone(tmp_path):
    _write_record(tmp_path)
    client = _client()
    client.add("GET", FORMATTER_URL, 403, content=b"denied")

    report = _publish(tmp_path, client, update_mode="complete")

    assert report.failed == 1
    assert "HTTP 403" in report.errors[0]
    assert not client.calls_to("PUT")


def test_complete_with_something_else_than_xml_fails_alone(tmp_path):
    _write_record(tmp_path)
    client = _client()
    client.add("GET", FORMATTER_URL, 200, content=b"<html><body>login")

    report = _publish(tmp_path, client, update_mode="complete")

    assert report.failed == 1
    assert not client.calls_to("PUT")


def test_complete_does_not_resolve_entities_of_the_catalog_answer(tmp_path):
    _write_record(tmp_path)
    secret_file = tmp_path / "secret.txt"
    secret_file.write_text("my secret", encoding="UTF-8")
    client = _client()
    client.add(
        "GET",
        FORMATTER_URL,
        200,
        content=(
            f"""<!DOCTYPE foo [<!ENTITY xxe SYSTEM "{secret_file.as_uri()}">]>
            <gmd:MD_Metadata xmlns:gmd="http://www.isotc211.org/2005/gmd"
                             xmlns:gco="http://www.isotc211.org/2005/gco">
                <gmd:fileIdentifier><gco:CharacterString>&xxe;</gco:CharacterString></gmd:fileIdentifier>
            </gmd:MD_Metadata>"""
        ).encode(),
    )

    _publish(tmp_path, client, update_mode="complete")

    assert not any(call.data and b"my secret" in call.data for call in client.calls)


def test_identifier_is_escaped_in_the_url(tmp_path):
    _write_record(tmp_path, identifier="a/b c")
    client = _client()
    escaped_url = f"{RECORDS_URL}/a%2Fb%20c/formatters/xml"
    client.add("GET", escaped_url, 404)

    _publish(tmp_path, client, update_mode="complete")

    assert client.calls_to("GET", escaped_url)


# ##############################################################################
# ##### Stand alone program ########
# ##################################
if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
