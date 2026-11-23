#! python3  # noqa: E265

"""
Tests for `dicogis-cli publish --target geonetwork`, against a mocked HTTP API.

Usage from the repo root folder:
    pytest tests/test_cli_publish_geonetwork.py
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# standard library
import re
import sys
from datetime import date
from pathlib import Path

# 3rd party
import pytest
import responses
from lxml import etree
from responses import matchers
from typer.testing import CliRunner

# project
from dicogis.cli.main import dicogis_cli
from dicogis.export.catalog_record import CatalogRecord
from dicogis.export.to_iso19139 import record_to_iso19139


# ##############################################################################
# ########## Globals ###############
# ##################################

URL_BASE = "https://catalogue.example/geonetwork"
ME_URL = f"{URL_BASE}/srv/api/me"
RECORDS_URL = f"{URL_BASE}/srv/api/records"
IDENTIFIER = "6a4e5ba7-e7dd-533a-a57c-42632717ecfe"

runner = CliRunner()

# ##############################################################################
# ########## Fixtures ##############
# ##################################


@pytest.fixture
def records_folder(tmp_path: Path) -> Path:
    record = CatalogRecord(
        identifier=IDENTIFIER,
        title="title",
        abstract="abstract",
        language="fre",
        metadata_date=date(2026, 11, 8),
        spatial_representation="vector",
    )
    (tmp_path / "a.xml").write_bytes(etree.tostring(record_to_iso19139(record)))
    return tmp_path


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch) -> None:
    """Options must come from the tests, and notifications stay silent."""
    for name in (
        "DICOGIS_PUBLISH_TARGET",
        "DICOGIS_GEONETWORK_URL_BASE",
        "DICOGIS_GEONETWORK_USERNAME",
        "DICOGIS_GEONETWORK_PASSWORD",
        "DICOGIS_GEONETWORK_GROUP",
        "DICOGIS_UDATA_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(
        "dicogis.cli.cmd_publish.send_system_notify", lambda **kwargs: None
    )


# ##############################################################################
# ########## Functions #############
# ##################################


def _mock_catalog() -> None:
    responses.get(
        ME_URL,
        json={"username": "editor"},
        headers={"Set-Cookie": "XSRF-TOKEN=token-1; Path=/"},
    )
    responses.put(RECORDS_URL, json={"numberOfRecordsWithErrors": 0}, status=201)


def _arguments(records_folder: Path, *extra: str) -> list[str]:
    return [
        "publish",
        "--target",
        "geonetwork",
        "--input-folder",
        str(records_folder),
        "--geonetwork-url-base",
        URL_BASE,
        "--geonetwork-group",
        "2",
        "--no-opt-notify-sound",
        *extra,
    ]


# ##############################################################################
# ########## Tests ##################
# ##################################


@responses.activate
def test_publish_to_geonetwork(records_folder):
    _mock_catalog()

    result = runner.invoke(
        dicogis_cli,
        _arguments(
            records_folder,
            "--geonetwork-username",
            "editor",
            "--geonetwork-password",
            "s3cret",
            "--geonetwork-categories",
            "1, 3",
            "--geonetwork-publish-to-all",
            "--geonetwork-reject-if-invalid",
        ),
    )

    assert result.exit_code == 0, result.output
    assert "1 files published" in result.output
    put_url = responses.calls[1].request.url
    assert "group=2" in put_url
    assert "category=1&category=3" in put_url
    assert "publishToAll=true" in put_url
    assert "rejectIfInvalid=true" in put_url
    assert responses.calls[1].request.headers["X-XSRF-TOKEN"] == "token-1"


@responses.activate
def test_options_from_the_environment(records_folder, monkeypatch):
    _mock_catalog()
    monkeypatch.setenv("DICOGIS_PUBLISH_TARGET", "geonetwork")
    monkeypatch.setenv("DICOGIS_GEONETWORK_URL_BASE", URL_BASE)
    monkeypatch.setenv("DICOGIS_GEONETWORK_USERNAME", "editor")
    monkeypatch.setenv("DICOGIS_GEONETWORK_PASSWORD", "s3cret")
    monkeypatch.setenv("DICOGIS_GEONETWORK_GROUP", "2")

    result = runner.invoke(
        dicogis_cli, ["publish", "--input-folder", str(records_folder)]
    )

    assert result.exit_code == 0, result.output
    assert len(responses.calls) == 2


@responses.activate
def test_account_is_asked_for_when_not_set(records_folder):
    _mock_catalog()

    result = runner.invoke(
        dicogis_cli, _arguments(records_folder), input="editor\ns3cret\n"
    )

    assert result.exit_code == 0, result.output
    assert "s3cret" not in result.output
    assert responses.calls[0].request.headers["Authorization"].startswith("Basic ")


@responses.activate
def test_update_mode_complete_reports_added_fields(records_folder):
    _mock_catalog()
    responses.get(
        f"{RECORDS_URL}/{IDENTIFIER}/formatters/xml",
        body=(
            '<gmd:MD_Metadata xmlns:gmd="http://www.isotc211.org/2005/gmd"'
            ' xmlns:gco="http://www.isotc211.org/2005/gco">'
            "<gmd:identificationInfo><gmd:MD_DataIdentification>"
            "</gmd:MD_DataIdentification></gmd:identificationInfo>"
            "</gmd:MD_Metadata>"
        ),
        match=[
            matchers.query_param_matcher(
                {"approved": "false", "increasePopularity": "false"}
            )
        ],
    )

    result = runner.invoke(
        dicogis_cli,
        _arguments(
            records_folder,
            "--geonetwork-username",
            "editor",
            "--geonetwork-password",
            "s3cret",
            "--geonetwork-update-mode",
            "complete",
        ),
    )

    assert result.exit_code == 0, result.output
    assert "a.xml: added" in result.output
    assert "abstract" in result.output


@responses.activate
def test_refused_account_exits_with_an_error(records_folder):
    responses.get(ME_URL, status=204)

    result = runner.invoke(
        dicogis_cli,
        _arguments(
            records_folder,
            "--geonetwork-username",
            "editor",
            "--geonetwork-password",
            "wrong",
        ),
    )

    assert result.exit_code == 1
    assert "anonymous" in result.output


@responses.activate
def test_unreachable_catalog_exits_with_an_error(records_folder):
    result = runner.invoke(
        dicogis_cli,
        _arguments(
            records_folder,
            "--geonetwork-username",
            "editor",
            "--geonetwork-password",
            "s3cret",
        ),
    )

    assert result.exit_code == 1
    assert "Traceback" not in result.output


def test_missing_group_exits_with_an_error(records_folder):
    result = runner.invoke(
        dicogis_cli,
        [
            "publish",
            "--target",
            "geonetwork",
            "--input-folder",
            str(records_folder),
            "--geonetwork-url-base",
            URL_BASE,
            "--geonetwork-username",
            "editor",
            "--geonetwork-password",
            "s3cret",
        ],
    )

    assert result.exit_code == 1
    assert "group" in result.output


def test_geonetwork_does_not_ask_for_the_udata_key(records_folder):
    """--udata-api-key used to be prompted for whatever the target."""
    result = runner.invoke(
        dicogis_cli,
        _arguments(
            records_folder,
            "--geonetwork-username",
            "editor",
            "--geonetwork-password",
            "s3cret",
            "--geonetwork-group",
            "not_a_number",
        ),
        input="",
    )

    assert "uData API key" not in result.output


@responses.activate
def test_udata_stays_the_default_target_and_asks_for_its_key(tmp_path):
    (tmp_path / "a.json").write_text("{}", encoding="UTF-8")
    responses.get("https://demo.data.gouv.fr/api/1/me/datasets/", json=[])

    result = runner.invoke(
        dicogis_cli,
        ["publish", "--input-folder", str(tmp_path), "--no-opt-notify-sound"],
        input="my-key\nmy-key\n",
    )

    assert result.exit_code == 0, result.output
    assert "uData API key" in result.output
    assert responses.calls[0].request.headers["X-API-KEY"] == "my-key"


def test_help_lists_the_options():
    result = runner.invoke(
        dicogis_cli,
        ["publish", "--help"],
        env={"COLUMNS": "200", "TERMINAL_WIDTH": "200", "NO_COLOR": "1"},
    )

    assert result.exit_code == 0
    # on GitHub Actions, Typer forces styles that NO_COLOR doesn't remove
    output = re.sub(r"\x1b\[[0-9;]*m", "", result.output)
    for option in ("--target", "--geonetwork-url-base", "--geonetwork-update-mode"):
        assert option in output


# ##############################################################################
# ##### Stand alone program ########
# ##################################
if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
