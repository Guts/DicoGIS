#! python3  # noqa: E265


"""
Tests for the uData publication core, called directly (the CLI command is
covered by tests/test_cli_publish_udata.py).

Usage from the repo root folder:
    pytest tests/test_publishing_udata.py
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# standard library
import json
import sys
from pathlib import Path

# 3rd party
import pytest
import responses
from responses import matchers

# project
from dicogis.publishing.settings import DEFAULT_PUBLISH_TIMEOUT
from dicogis.publishing.udata import publish_metadata_folder


# ##############################################################################
# ########## Globals ###############
# ##################################

UDATA_API_URL_BASE = "https://udata-test.example/api/"
UDATA_API_VERSION = "1"

# ##############################################################################
# ########## Classes ###############
# ##################################


class _RecordingReporter:
    """ProgressReporter recording what it's told, asking to stop after some files."""

    def __init__(self, cancel_after: int | None = None) -> None:
        self.cancel_after = cancel_after
        self.total = None
        self.count = 0
        self.messages: list[str] = []

    def set_message(self, message: str) -> None:
        self.messages.append(message)

    def increment(self, amount: int = 1) -> None:
        self.count += amount

    def set_total(self, total: int) -> None:
        self.total = total

    def is_canceled(self) -> bool:
        return self.cancel_after is not None and self.count >= self.cancel_after


# ##############################################################################
# ########## Functions #############
# ##################################


def _write_json(folder: Path, filename: str, content: object) -> Path:
    file_path = folder / filename
    file_path.write_text(json.dumps(content), encoding="UTF-8")
    return file_path


def _dicogis_metadata(slug: str) -> dict:
    return {
        "title": slug,
        "slug": slug,
        "extras": {"dicogis_signature": f"sig-{slug}", "dicogis_version": "test"},
    }


# ##############################################################################
# ########## Tests ##################
# ##################################


@responses.activate
def test_each_file_is_counted_and_reported_once(tmp_path: Path) -> None:
    """One file per outcome: unreadable, not DicoGIS', already published, new.
    The progress is reported once per file, whatever its outcome."""
    (tmp_path / "a_broken.json").write_text("{not json", encoding="UTF-8")
    _write_json(tmp_path, "b_foreign.json", {"title": "not from DicoGIS"})
    _write_json(tmp_path, "c_published.json", _dicogis_metadata("already-there"))
    _write_json(tmp_path, "d_new.json", _dicogis_metadata("brand-new"))
    responses.get(
        f"{UDATA_API_URL_BASE}{UDATA_API_VERSION}/me/datasets/",
        json=[{"slug": "already-there"}],
        status=200,
    )
    responses.post(
        f"{UDATA_API_URL_BASE}{UDATA_API_VERSION}/datasets", json={}, status=201
    )
    reporter = _RecordingReporter()

    report = publish_metadata_folder(
        input_folder=tmp_path,
        udata_api_key="fake-api-key",
        udata_api_url_base=UDATA_API_URL_BASE,
        udata_api_version=UDATA_API_VERSION,
        progress_reporter=reporter,
    )

    assert (report.published, report.ignored, report.failed) == (1, 2, 1)
    assert len(report.errors) == 1
    assert report.canceled is False
    assert reporter.total == 4
    assert reporter.count == 4
    assert set(reporter.messages) == {
        "a_broken.json",
        "b_foreign.json",
        "c_published.json",
        "d_new.json",
    }


@responses.activate
def test_cancellation_stops_between_two_files_and_keeps_the_report(
    tmp_path: Path,
) -> None:
    _write_json(tmp_path, "a.json", _dicogis_metadata("a"))
    _write_json(tmp_path, "b.json", _dicogis_metadata("b"))
    _write_json(tmp_path, "c.json", _dicogis_metadata("c"))
    responses.get(
        f"{UDATA_API_URL_BASE}{UDATA_API_VERSION}/me/datasets/", json=[], status=200
    )
    responses.post(
        f"{UDATA_API_URL_BASE}{UDATA_API_VERSION}/datasets", json={}, status=201
    )
    reporter = _RecordingReporter(cancel_after=2)

    report = publish_metadata_folder(
        input_folder=tmp_path,
        udata_api_key="fake-api-key",
        udata_api_url_base=UDATA_API_URL_BASE,
        udata_api_version=UDATA_API_VERSION,
        progress_reporter=reporter,
    )

    assert report.canceled is True
    assert report.published == 2
    assert len(responses.calls) == 3


@responses.activate
@pytest.mark.parametrize(
    ("timeout", "env_value", "expected"),
    [
        (None, None, DEFAULT_PUBLISH_TIMEOUT),
        (None, "12.5", 12.5),
        (None, "not_a_number", DEFAULT_PUBLISH_TIMEOUT),
        (None, "-1", DEFAULT_PUBLISH_TIMEOUT),
        (3.0, "12.5", 3.0),
    ],
)
def test_every_request_has_a_timeout(
    tmp_path: Path, monkeypatch, timeout, env_value, expected
) -> None:
    """Without one, an unresponsive catalog would block forever, thread included."""
    _write_json(tmp_path, "new.json", _dicogis_metadata("brand-new"))
    if env_value is None:
        monkeypatch.delenv("DICOGIS_PUBLISH_TIMEOUT", raising=False)
    else:
        monkeypatch.setenv("DICOGIS_PUBLISH_TIMEOUT", env_value)
    has_timeout = matchers.request_kwargs_matcher({"timeout": expected})
    responses.get(
        f"{UDATA_API_URL_BASE}{UDATA_API_VERSION}/me/datasets/",
        json=[],
        status=200,
        match=[has_timeout],
    )
    responses.post(
        f"{UDATA_API_URL_BASE}{UDATA_API_VERSION}/datasets",
        json={},
        status=201,
        match=[has_timeout],
    )

    report = publish_metadata_folder(
        input_folder=tmp_path,
        udata_api_key="fake-api-key",
        udata_api_url_base=UDATA_API_URL_BASE,
        udata_api_version=UDATA_API_VERSION,
        timeout=timeout,
    )

    assert report.published == 1


@responses.activate
def test_failed_post_is_counted_as_failed(tmp_path: Path) -> None:
    _write_json(tmp_path, "new.json", _dicogis_metadata("brand-new"))
    responses.get(
        f"{UDATA_API_URL_BASE}{UDATA_API_VERSION}/me/datasets/", json=[], status=200
    )
    responses.post(
        f"{UDATA_API_URL_BASE}{UDATA_API_VERSION}/datasets", json={}, status=500
    )

    report = publish_metadata_folder(
        input_folder=tmp_path,
        udata_api_key="fake-api-key",
        udata_api_url_base=UDATA_API_URL_BASE,
        udata_api_version=UDATA_API_VERSION,
    )

    assert (report.published, report.ignored, report.failed) == (0, 0, 1)
    assert "failed" in report.errors[0]


# ##############################################################################
# ##### Stand alone program ########
# ##################################
if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
