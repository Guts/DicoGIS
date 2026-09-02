#! python3  # noqa: E265

"""
Usage from the repo root folder:
    python -m unittest tests.test_cli_publish_udata

These tests exercise the `dicogis-cli publish` logic (`dicogis.cli.cmd_publish.publish`)
against a mocked udata HTTP API (using the `responses` library), so they can run in CI
without requiring a full udata stack (MongoDB, Elasticsearch, Redis, uData...).
"""

# ############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

# 3rd party
import responses
import typer

# project
from dicogis.cli.cmd_publish import publish


# ############################################################################
# ########## Globals ###############
# ##################################

UDATA_API_URL_BASE = "https://udata-test.example/api/"
UDATA_API_VERSION = "1"

# ############################################################################
# ########## Functions #############
# ##################################


def make_udata_metadata_file(
    folder: Path, filename: str, title: str, slug: str, signature: str
) -> Path:
    """Write a minimal udata-flavored JSON metadata file, similar to what
    `dicogis-cli inventory --output-format udata` generates.
    """
    metadata = {
        "title": title,
        "slug": slug,
        "description": "Sample dataset description.",
        "extras": {
            "dicogis_original_path": f"/data/{filename}",
            "dicogis_signature": signature,
            "dicogis_version": "test-dev",
        },
        "tags": ["ESRI Shapefile", "ESRI Shapefile", "srs_undefined"],
    }
    filepath = folder / filename
    with filepath.open(mode="w", encoding="UTF-8") as f:
        json.dump(metadata, f)
    return filepath


# ############################################################################
# ########## Classes ###############
# ##################################


class TestCliPublishUdata(unittest.TestCase):
    """Test suite mocking a udata catalog API to validate the publish CLI command."""

    def setUp(self) -> None:
        """Prepare a temporary input folder and mock system notifications out."""
        self.tmp_dir = TemporaryDirectory()
        self.input_folder = Path(self.tmp_dir.name)
        self.notify_patcher = patch("dicogis.cli.cmd_publish.send_system_notify")
        self.mock_notify = self.notify_patcher.start()

    def tearDown(self) -> None:
        """Clean up patches and temporary files."""
        self.notify_patcher.stop()
        self.tmp_dir.cleanup()

    def assertPublishReport(self, published: int, ignored: int, failed: int) -> None:
        """Assert the end-of-run notification matches the expected counters."""
        self.mock_notify.assert_called_once_with(
            notification_title="DicoGIS publication ended",
            notification_message=f"{published} published, {ignored} ignored,"
            f"{failed} failed.",
            notification_sound=False,
        )

    @responses.activate
    def test_publish_new_datasets_are_posted_to_udata(self) -> None:
        """Two new metadata files should be published as two API calls."""
        make_udata_metadata_file(
            self.input_folder, "dataset-a.json", "Dataset A", "dataset-a", "sig-a"
        )
        make_udata_metadata_file(
            self.input_folder, "dataset-b.json", "Dataset B", "dataset-b", "sig-b"
        )

        responses.get(
            f"{UDATA_API_URL_BASE}{UDATA_API_VERSION}/me/datasets/",
            json=[],
            status=200,
        )
        responses.post(
            f"{UDATA_API_URL_BASE}{UDATA_API_VERSION}/datasets",
            json={"id": "generated-id", "slug": "generated-slug"},
            status=201,
        )

        publish(
            input_folder=self.input_folder,
            udata_api_key="fake-api-key",
            udata_api_url_base=UDATA_API_URL_BASE,
            udata_api_version=UDATA_API_VERSION,
            udata_organization_id=None,
            opt_notify_sound=False,
            verbose=True,
        )

        post_calls = [call for call in responses.calls if call.request.method == "POST"]
        self.assertEqual(len(post_calls), 2)
        published_slugs = set()
        for call in post_calls:
            self.assertEqual(call.request.headers["X-API-KEY"], "fake-api-key")
            payload = json.loads(call.request.body)
            published_slugs.add(payload["slug"])
        self.assertSetEqual(published_slugs, {"dataset-a", "dataset-b"})

        self.assertPublishReport(published=2, ignored=0, failed=0)

    @responses.activate
    def test_publish_skips_dataset_already_published_by_signature(self) -> None:
        """A dataset whose signature is already published must be skipped."""
        make_udata_metadata_file(
            self.input_folder,
            "already-published.json",
            "Already published",
            "already-published",
            "sig-already-published",
        )
        make_udata_metadata_file(
            self.input_folder,
            "new-dataset.json",
            "New dataset",
            "new-dataset",
            "sig-new",
        )

        responses.get(
            f"{UDATA_API_URL_BASE}{UDATA_API_VERSION}/me/datasets/",
            json=[
                {
                    "slug": "some-other-slug",
                    "extras": {"dicogis_signature": "sig-already-published"},
                }
            ],
            status=200,
        )
        responses.post(
            f"{UDATA_API_URL_BASE}{UDATA_API_VERSION}/datasets",
            json={"id": "generated-id", "slug": "generated-slug"},
            status=201,
        )

        publish(
            input_folder=self.input_folder,
            udata_api_key="fake-api-key",
            udata_api_url_base=UDATA_API_URL_BASE,
            udata_api_version=UDATA_API_VERSION,
            udata_organization_id=None,
            opt_notify_sound=False,
            verbose=True,
        )

        post_calls = [call for call in responses.calls if call.request.method == "POST"]
        self.assertEqual(len(post_calls), 1)
        payload = json.loads(post_calls[0].request.body)
        self.assertEqual(payload["slug"], "new-dataset")

        self.assertPublishReport(published=1, ignored=1, failed=0)

    @responses.activate
    def test_publish_skips_dataset_already_published_by_slug(self) -> None:
        """A dataset whose slug is already published must be skipped, even with a new signature."""
        make_udata_metadata_file(
            self.input_folder,
            "already-published.json",
            "Already published",
            "already-published",
            "sig-changed-but-same-slug",
        )

        responses.get(
            f"{UDATA_API_URL_BASE}{UDATA_API_VERSION}/me/datasets/",
            json=[
                {
                    "slug": "already-published",
                    "extras": {"dicogis_signature": "sig-original"},
                }
            ],
            status=200,
        )
        responses.post(
            f"{UDATA_API_URL_BASE}{UDATA_API_VERSION}/datasets",
            json={"id": "generated-id", "slug": "generated-slug"},
            status=201,
        )

        publish(
            input_folder=self.input_folder,
            udata_api_key="fake-api-key",
            udata_api_url_base=UDATA_API_URL_BASE,
            udata_api_version=UDATA_API_VERSION,
            udata_organization_id=None,
            opt_notify_sound=False,
            verbose=True,
        )

        post_calls = [call for call in responses.calls if call.request.method == "POST"]
        self.assertEqual(len(post_calls), 0)

        self.assertPublishReport(published=0, ignored=1, failed=0)

    @responses.activate
    def test_publish_to_organization_catalog(self) -> None:
        """When an organization id is set, datasets must be attached to it."""
        organization_id = "666f6f2d6261722d71757578"
        make_udata_metadata_file(
            self.input_folder,
            "org-dataset.json",
            "Org dataset",
            "org-dataset",
            "sig-org",
        )

        responses.get(
            f"{UDATA_API_URL_BASE}{UDATA_API_VERSION}/organizations/"
            f"{organization_id}/datasets/",
            json={"data": []},
            status=200,
        )
        responses.post(
            f"{UDATA_API_URL_BASE}{UDATA_API_VERSION}/datasets",
            json={"id": "generated-id", "slug": "generated-slug"},
            status=201,
        )

        publish(
            input_folder=self.input_folder,
            udata_api_key="fake-api-key",
            udata_api_url_base=UDATA_API_URL_BASE,
            udata_api_version=UDATA_API_VERSION,
            udata_organization_id=organization_id,
            opt_notify_sound=False,
            verbose=True,
        )

        post_calls = [call for call in responses.calls if call.request.method == "POST"]
        self.assertEqual(len(post_calls), 1)
        payload = json.loads(post_calls[0].request.body)
        self.assertEqual(payload["organization"], {"id": organization_id})

        self.assertPublishReport(published=1, ignored=0, failed=0)

    @responses.activate
    def test_publish_counts_api_failures_without_crashing(self) -> None:
        """A dataset rejected by the API must be counted as failed; others still get processed."""
        make_udata_metadata_file(
            self.input_folder, "broken.json", "Broken dataset", "broken", "sig-broken"
        )
        make_udata_metadata_file(
            self.input_folder, "ok.json", "OK dataset", "ok-dataset", "sig-ok"
        )

        responses.get(
            f"{UDATA_API_URL_BASE}{UDATA_API_VERSION}/me/datasets/",
            json=[],
            status=200,
        )

        def post_callback(request):
            payload = json.loads(request.body)
            if payload["slug"] == "broken":
                return (400, {}, json.dumps({"message": "invalid dataset"}))
            return (
                201,
                {},
                json.dumps({"id": "generated-id", "slug": "generated-slug"}),
            )

        responses.add_callback(
            responses.POST,
            f"{UDATA_API_URL_BASE}{UDATA_API_VERSION}/datasets",
            callback=post_callback,
            content_type="application/json",
        )

        publish(
            input_folder=self.input_folder,
            udata_api_key="fake-api-key",
            udata_api_url_base=UDATA_API_URL_BASE,
            udata_api_version=UDATA_API_VERSION,
            udata_organization_id=None,
            opt_notify_sound=False,
            verbose=True,
        )

        post_calls = [call for call in responses.calls if call.request.method == "POST"]
        self.assertEqual(len(post_calls), 2)

        self.assertPublishReport(published=1, ignored=0, failed=1)

    @responses.activate
    def test_publish_ignores_non_dicogis_json_files(self) -> None:
        """A JSON file without DicoGIS extras must be ignored, not published."""
        foreign_file = self.input_folder / "not-dicogis.json"
        with foreign_file.open(mode="w", encoding="UTF-8") as f:
            json.dump({"title": "Unrelated file", "extras": {}}, f)

        responses.get(
            f"{UDATA_API_URL_BASE}{UDATA_API_VERSION}/me/datasets/",
            json=[],
            status=200,
        )

        publish(
            input_folder=self.input_folder,
            udata_api_key="fake-api-key",
            udata_api_url_base=UDATA_API_URL_BASE,
            udata_api_version=UDATA_API_VERSION,
            udata_organization_id=None,
            opt_notify_sound=False,
            verbose=True,
        )

        post_calls = [call for call in responses.calls if call.request.method == "POST"]
        self.assertEqual(len(post_calls), 0)

        self.assertPublishReport(published=0, ignored=1, failed=0)

    @responses.activate
    def test_publish_survives_json_files_without_extras(self) -> None:
        """A JSON file carrying no "extras" key at all, or not even an object,
        must be ignored like any other foreign file.

        Regression: the DicoGIS filter did `data.get("extras").get(...)`, which
        raised AttributeError on such a file. Being raised outside the loop's
        try/except, it aborted the whole run: every remaining file went
        unpublished, and the command died on a traceback.
        """
        no_extras_file = self.input_folder / "no-extras.json"
        with no_extras_file.open(mode="w", encoding="UTF-8") as f:
            json.dump({"title": "No extras at all"}, f)

        null_extras_file = self.input_folder / "null-extras.json"
        with null_extras_file.open(mode="w", encoding="UTF-8") as f:
            json.dump({"title": "Null extras", "extras": None}, f)

        json_array_file = self.input_folder / "an-array.json"
        with json_array_file.open(mode="w", encoding="UTF-8") as f:
            json.dump([{"title": "Not even an object"}], f)

        # a genuine DicoGIS file, listed last alphabetically to prove the run
        # reaches it instead of dying on one of the files above
        make_udata_metadata_file(
            self.input_folder, "z-dataset.json", "Dataset Z", "dataset-z", "sig-z"
        )

        responses.get(
            f"{UDATA_API_URL_BASE}{UDATA_API_VERSION}/me/datasets/",
            json=[],
            status=200,
        )
        responses.post(
            f"{UDATA_API_URL_BASE}{UDATA_API_VERSION}/datasets",
            json={"id": "new-dataset-z"},
            status=201,
        )

        publish(
            input_folder=self.input_folder,
            udata_api_key="fake-api-key",
            udata_api_url_base=UDATA_API_URL_BASE,
            udata_api_version=UDATA_API_VERSION,
            udata_organization_id=None,
            opt_notify_sound=False,
            verbose=True,
        )

        post_calls = [call for call in responses.calls if call.request.method == "POST"]
        self.assertEqual(len(post_calls), 1)
        self.assertEqual(json.loads(post_calls[0].request.body)["slug"], "dataset-z")

        self.assertPublishReport(published=1, ignored=3, failed=0)

    @responses.activate
    def test_publish_is_not_blocked_by_a_catalog_dataset_without_signature(
        self,
    ) -> None:
        """A catalog holding datasets that DicoGIS did not publish (hence with
        no dicogis_signature) must not prevent publishing a file that has none
        either: two missing values used to compare equal, marking the file as
        already published.
        """
        unsigned_file = self.input_folder / "unsigned.json"
        with unsigned_file.open(mode="w", encoding="UTF-8") as f:
            json.dump(
                {
                    "title": "Hand-written but DicoGIS-flavored",
                    "slug": "hand-written",
                    "extras": {"dicogis_version": "test-dev"},
                },
                f,
            )

        responses.get(
            f"{UDATA_API_URL_BASE}{UDATA_API_VERSION}/me/datasets/",
            json=[{"title": "Someone else's dataset", "slug": "unrelated"}],
            status=200,
        )
        responses.post(
            f"{UDATA_API_URL_BASE}{UDATA_API_VERSION}/datasets",
            json={"id": "new-hand-written"},
            status=201,
        )

        publish(
            input_folder=self.input_folder,
            udata_api_key="fake-api-key",
            udata_api_url_base=UDATA_API_URL_BASE,
            udata_api_version=UDATA_API_VERSION,
            udata_organization_id=None,
            opt_notify_sound=False,
            verbose=True,
        )

        post_calls = [call for call in responses.calls if call.request.method == "POST"]
        self.assertEqual(len(post_calls), 1)

        self.assertPublishReport(published=1, ignored=0, failed=0)

    def test_publish_without_input_folder_exits(self) -> None:
        """--input-folder defaults to None, which publish_metadata_folder()
        used to dereference as `None.glob("*.json")`: an AttributeError
        traceback instead of a usage error.
        """
        with self.assertRaises(typer.Exit) as raised:
            publish(
                input_folder=None,
                udata_api_key="fake-api-key",
                udata_api_url_base=UDATA_API_URL_BASE,
                udata_api_version=UDATA_API_VERSION,
                udata_organization_id=None,
                opt_notify_sound=False,
            )

        self.assertEqual(raised.exception.exit_code, 1)
        # the guard runs before anything is attempted: no HTTP call, no
        # end-of-run notification
        self.assertEqual(len(responses.calls), 0)
        self.mock_notify.assert_not_called()


if __name__ == "__main__":
    unittest.main()
