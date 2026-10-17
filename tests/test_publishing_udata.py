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

# project
from dicogis.publishing.udata import publish_metadata_folder


# ##############################################################################
# ########## Globals ###############
# ##################################

UDATA_API_URL_BASE = "https://udata-test.example/api/"
UDATA_API_VERSION = "1"

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
    The progress callback is called once per file, whatever its outcome."""
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
    progress_calls: list[tuple[int, int, str]] = []

    report = publish_metadata_folder(
        input_folder=tmp_path,
        udata_api_key="fake-api-key",
        udata_api_url_base=UDATA_API_URL_BASE,
        udata_api_version=UDATA_API_VERSION,
        progress_callback=lambda done, total, json_file: progress_calls.append(
            (done, total, json_file.name)
        ),
    )

    assert (report.published, report.ignored, report.failed) == (1, 2, 1)
    assert len(report.errors) == 1
    assert [done for done, _, _ in progress_calls] == [1, 2, 3, 4]
    assert {name for _, _, name in progress_calls} == {
        "a_broken.json",
        "b_foreign.json",
        "c_published.json",
        "d_new.json",
    }
    assert all(total == 4 for _, total, _ in progress_calls)


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
