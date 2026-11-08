#! python3  # noqa: E265

"""
Publication against a real GeoNetwork, through whichever HTTP backend is selected.

Skipped unless DICOGIS_TEST_GEONETWORK_URL is set, which the workflow
.github/workflows/tester_geonetwork_publish.yml does, after starting
tests/container/docker-compose.ci-geonetwork.yml. It runs in two environments: a plain
Python one (requests backend), and the official QGIS image with
DICOGIS_HTTP_BACKEND=qgis, the only place where the QGIS backend and the QgsTask meet
the real QGIS.

Usage from the repo root folder, a GeoNetwork running:
    DICOGIS_TEST_GEONETWORK_URL=http://localhost:8080/geonetwork \
        pytest -o addopts="" tests/integration/test_geonetwork_publish.py
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# standard library
import time
from os import getenv
from pathlib import Path
from uuid import uuid4

# 3rd party
import pytest
from lxml import etree

# project
from dicogis.export.catalog_record import CatalogRecordSettings
from dicogis.export.to_iso19139 import (
    ISO19139_NAMESPACES,
    MetadatasetSerializerIso19139,
)
from dicogis.models.database_connection import DatabaseConnection
from dicogis.models.metadataset import (
    MetaDatabaseFlat,
    MetaDatabaseTable,
    MetaRasterDataset,
    MetaVectorDataset,
)
from dicogis.publishing.geonetwork import (
    GeonetworkAuthenticationError,
    GeonetworkCredentials,
    GeonetworkSession,
    publish_metadata_folder,
)
from dicogis.utils.http import get_http_client


# ##############################################################################
# ########## Globals ###############
# ##################################

GEONETWORK_URL = getenv("DICOGIS_TEST_GEONETWORK_URL")
ADMIN = GeonetworkCredentials(
    username=getenv("DICOGIS_TEST_GEONETWORK_USERNAME", "admin"),
    password=getenv("DICOGIS_TEST_GEONETWORK_PASSWORD", "admin"),
)
# the group coming with a fresh GeoNetwork
GROUP = getenv("DICOGIS_TEST_GEONETWORK_GROUP", "2")
IDENT = "gmd:identificationInfo/gmd:MD_DataIdentification"
TITLE_PATH = f"{IDENT}/gmd:citation/gmd:CI_Citation/gmd:title/gco:CharacterString"
ABSTRACT_PATH = f"{IDENT}/gmd:abstract/gco:CharacterString"

pytestmark = pytest.mark.skipif(
    not GEONETWORK_URL, reason="DICOGIS_TEST_GEONETWORK_URL is not set"
)

# ##############################################################################
# ########## Fixtures ##############
# ##################################


@pytest.fixture(scope="module", autouse=True)
def qgis_application():
    """Start QGIS when testing its backend: nothing works without a QgsApplication."""
    if getenv("DICOGIS_HTTP_BACKEND") != "qgis":
        yield None
        return
    from qgis.core import QgsApplication

    application = QgsApplication([], False)
    application.initQgis()
    yield application
    application.exitQgis()


@pytest.fixture
def session() -> GeonetworkSession:
    """Administrator session, to look at what the catalog holds."""
    opened_session = GeonetworkSession(
        http_client=get_http_client(),
        url_base=GEONETWORK_URL,
        credentials=ADMIN,
        timeout=60.0,
    )
    opened_session.open()
    return opened_session


# ##############################################################################
# ########## Functions #############
# ##################################


def _metadatasets(run_id: str) -> list:
    """Build a dataset of each kind, the location making its identifier unique per run.

    Returns:
        metadatasets, each one having its own way of challenging the XSD
    """
    common = dict(
        format_gdal_long_name="ESRI Shapefile",
        format_gdal_short_name="ESRI Shapefile",
        crs_name="WGS 84",
        crs_registry="EPSG",
        crs_registry_code="4326",
        bbox_wgs84=(1.0, 2.0, 3.0, 4.0),
    )
    return [
        MetaVectorDataset(name="vector", path=Path(f"{run_id}/vector.shp"), **common),
        MetaRasterDataset(name="raster", path=Path(f"{run_id}/raster.tif"), **common),
        # no date at all
        MetaDatabaseTable(
            name=f"public.table_{run_id}",
            database_connection=DatabaseConnection(
                database_name="db", host="h", port=5432, user_name="u"
            ),
            **common,
        ),
        MetaDatabaseFlat(
            name="database",
            path=Path(f"{run_id}/database.gpkg"),
            format_gdal_long_name="GeoPackage",
            format_gdal_short_name="GPKG",
            layers=[
                MetaVectorDataset(
                    name="layer", dataset_type="data_layer", geometry_type="Point"
                )
            ],
        ),
        # neither CRS nor extent
        MetaVectorDataset(
            name="no_crs",
            path=Path(f"{run_id}/no_crs.shp"),
            format_gdal_long_name="ESRI Shapefile",
            format_gdal_short_name="ESRI Shapefile",
            crs_name="srs_undefined",
            crs_registry="srs_undefined",
            crs_registry_code="srs_no_epsg",
        ),
    ]


def _export(folder: Path, metadatasets: list) -> list[Path]:
    serializer = MetadatasetSerializerIso19139(
        settings=CatalogRecordSettings(
            language="fre",
            contact_organisation="DicoGIS CI",
            contact_email="ci@example.org",
        ),
        localized_strings={},
        output_path=folder,
    )
    return [serializer.serialize_metadaset(metadataset) for metadataset in metadatasets]


def _publish(folder: Path, **overrides):
    kwargs = dict(
        input_folder=folder,
        url_base=GEONETWORK_URL,
        group=GROUP,
        credentials=ADMIN,
        http_client=get_http_client(),
        timeout=60.0,
    )
    kwargs.update(overrides)
    return publish_metadata_folder(**kwargs)


def _catalog_record(session: GeonetworkSession, identifier: str) -> etree._Element:
    response = session.request(
        "GET",
        f"records/{identifier}/formatters/xml",
        params={"approved": "false", "increasePopularity": "false"},
        headers={"Accept": "application/xml"},
    )
    response.raise_for_status()
    return etree.fromstring(response.content)


def _text(root: etree._Element, xpath: str) -> str | None:
    return root.findtext(xpath, namespaces=ISO19139_NAMESPACES)


# ##############################################################################
# ########## Tests ##################
# ##################################


def test_every_kind_of_record_is_valid_against_the_xsd(tmp_path, session):
    """rejectIfInvalid has the catalog validate them against its XSD."""
    metadatasets = _metadatasets(uuid4().hex)
    _export(tmp_path, metadatasets)

    report = _publish(tmp_path, reject_if_invalid=True)

    assert report.errors == []
    assert report.published == len(metadatasets)
    for metadataset in metadatasets:
        record = _catalog_record(session, metadataset.uuid)
        assert (
            _text(record, "gmd:fileIdentifier/gco:CharacterString") == metadataset.uuid
        )


def test_publishing_twice_keeps_one_record(tmp_path, session):
    metadataset = _metadatasets(uuid4().hex)[0]
    _export(tmp_path, [metadataset])

    first_report = _publish(tmp_path, reject_if_invalid=True)
    second_report = _publish(tmp_path, reject_if_invalid=True)

    assert (first_report.published, second_report.published) == (1, 1)
    assert second_report.errors == []
    assert _catalog_record(session, metadataset.uuid) is not None
    # the catalog went through an update, not an insertion refused for a duplicate
    assert second_report.failed == 0


def test_complete_fills_the_empty_fields_and_keeps_the_others(tmp_path, session):
    metadataset = _metadatasets(uuid4().hex)[0]
    local_folder = tmp_path / "local"
    remote_folder = tmp_path / "remote"
    local_file = _export(local_folder, [metadataset])[0]

    # in the catalog: a title changed by hand and no abstract
    edited = etree.parse(str(local_file)).getroot()
    edited.find(TITLE_PATH, ISO19139_NAMESPACES).text = "Title edited by hand"
    abstract = edited.find(f"{IDENT}/gmd:abstract", ISO19139_NAMESPACES)
    abstract.remove(abstract[0])
    remote_folder.mkdir()
    (remote_folder / "edited.xml").write_bytes(etree.tostring(edited))
    assert _publish(remote_folder).published == 1

    report = _publish(local_folder, update_mode="complete")

    assert report.errors == []
    assert report.added_fields == {local_file.name: ["abstract"]}
    record = _catalog_record(session, metadataset.uuid)
    assert _text(record, TITLE_PATH) == "Title edited by hand"
    assert _text(record, ABSTRACT_PATH)

    # nothing left to add
    second_report = _publish(local_folder, update_mode="complete")
    assert second_report.up_to_date == 1
    assert second_report.published == 0


def test_complete_inserts_what_the_catalog_does_not_have(tmp_path, session):
    metadataset = _metadatasets(uuid4().hex)[0]
    _export(tmp_path, [metadataset])

    report = _publish(tmp_path, update_mode="complete")

    assert report.published == 1
    assert report.added_fields == {}
    assert _catalog_record(session, metadataset.uuid) is not None


def test_wrong_password_is_refused(tmp_path):
    _export(tmp_path, _metadatasets(uuid4().hex)[:1])

    with pytest.raises(GeonetworkAuthenticationError):
        _publish(tmp_path, credentials=GeonetworkCredentials("admin", "wrong"))


def test_unknown_group_fails_each_file_with_the_catalog_explanation(tmp_path):
    _export(tmp_path, _metadatasets(uuid4().hex)[:1])

    report = _publish(tmp_path, group="999999")

    assert report.failed == 1
    assert "HTTP" in report.errors[0]


@pytest.mark.skipif(
    getenv("DICOGIS_HTTP_BACKEND") != "qgis", reason="needs a running QGIS"
)
def test_publication_runs_in_a_real_task(tmp_path, session):
    from qgis.core import QgsApplication

    from dicogis.publishing.qgis_task import start_publish_task
    from dicogis.utils.qgis_runtime import qgis_application_is_running

    assert qgis_application_is_running()
    metadataset = _metadatasets(uuid4().hex)[0]
    _export(tmp_path, [metadataset])
    reports, errors = [], []

    def _run(progress_reporter, feedback):
        return publish_metadata_folder(
            input_folder=tmp_path,
            url_base=GEONETWORK_URL,
            group=GROUP,
            credentials=ADMIN,
            http_client=get_http_client(feedback=feedback),
            progress_reporter=progress_reporter,
            timeout=60.0,
        )

    task = start_publish_task("DicoGIS CI", _run, reports.append, errors.append)

    deadline = time.monotonic() + 120
    while not reports and not errors and time.monotonic() < deadline:
        QgsApplication.processEvents()
        time.sleep(0.05)

    assert task is not None
    assert errors == []
    assert reports[0].published == 1
    assert _catalog_record(session, metadataset.uuid) is not None


# ##############################################################################
# ##### Stand alone program ########
# ##################################
if __name__ == "__main__":
    pytest.main(["-o", "addopts=", __file__])
