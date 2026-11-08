#! python3  # noqa: E265

"""
Tests for dicogis.export.catalog_record.

Usage from the repo root folder:
    pytest tests/test_export_catalog_record.py
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# standard library
from datetime import date, datetime
from pathlib import Path

# 3rd party
import pytest

# project
from dicogis.constants import AvailableLocales
from dicogis.export.catalog_record import CatalogRecord, CatalogRecordSettings
from dicogis.models.database_connection import DatabaseConnection
from dicogis.models.feature_attributes import AttributeField
from dicogis.models.metadataset import (
    MetaDatabaseFlat,
    MetaDatabaseTable,
    MetaDataset,
    MetaRasterDataset,
    MetaVectorDataset,
)


# ##############################################################################
# ########## Functions #############
# ##################################


def _vector(**overrides) -> MetaVectorDataset:
    values = dict(
        name="parcels",
        path=Path("data/parcels.shp"),
        format_gdal_long_name="ESRI Shapefile",
        format_gdal_short_name="ESRI Shapefile",
        crs_name="RGF93 v1 / Lambert-93",
        crs_registry="EPSG",
        crs_registry_code="2154",
        bbox_wgs84=(2.0, 48.0, 3.0, 49.0),
    )
    values.update(overrides)
    return MetaVectorDataset(**values)


def _layer(**overrides) -> MetaVectorDataset:
    values = dict(
        name="layer",
        dataset_type="data_layer",
        geometry_type="Point",
        features_objects_count=3,
        crs_name="WGS 84",
        crs_registry="EPSG",
        crs_registry_code="4326",
    )
    values.update(overrides)
    return MetaVectorDataset(**values)


# ##############################################################################
# ########## Tests ##################
# ##################################


def test_record_of_a_vector_dataset():
    metadataset = _vector(
        storage_date_created=datetime(2020, 1, 2, 3, 4),
        storage_date_updated=datetime(2021, 5, 6, 7, 8),
    )

    record = CatalogRecord.from_metadataset(metadataset)

    assert record.identifier == metadataset.uuid
    assert record.title == "parcels"
    assert record.spatial_representation == "vector"
    assert record.keywords == ("ESRI Shapefile", "RGF93 v1 / Lambert-93")
    assert record.crs_codes == ("EPSG:2154",)
    assert record.formats == ("ESRI Shapefile",)
    assert record.bbox_wgs84 == (2.0, 48.0, 3.0, 49.0)
    assert record.date_created == date(2020, 1, 2)
    assert record.date_revised == date(2021, 5, 6)
    assert record.metadata_date == date.today()


def test_raster_is_a_grid():
    metadataset = MetaRasterDataset(name="dem", path=Path("dem.tif"))

    assert CatalogRecord.from_metadataset(metadataset).spatial_representation == "grid"


def test_description_is_the_abstract_when_there_is_one():
    record = CatalogRecord.from_metadataset(_vector(description="Land parcels."))

    assert record.abstract == "Land parcels."


def test_generated_abstract_describes_the_dataset():
    metadataset = _vector(
        geometry_type="Polygon",
        features_objects_count=12,
        storage_size=2048,
        feature_attributes=[
            AttributeField(name="id", data_type="Integer", length=10, precision=0)
        ],
    )

    abstract = CatalogRecord.from_metadataset(metadataset).abstract

    assert "- Geometry type: Polygon" in abstract
    assert "- Features objects count: 12" in abstract
    assert "RGF93 v1 / Lambert-93 (EPSG:2154)" in abstract
    assert "| id | Integer | 10 | 0 |" in abstract


def test_abstract_is_never_empty():
    record = CatalogRecord.from_metadataset(
        MetaDataset(name="parcels", path=Path("parcels.shp"))
    )

    assert record.abstract == "parcels"


def test_abstract_never_holds_a_path():
    """as_markdown_description lists the dependencies with their absolute paths."""
    metadataset = _vector(
        name="parcels",
        path=Path("secret_folder/parcels.shp"),
        files_dependencies=[Path("secret_folder/parcels.dbf")],
    )

    assert "secret_folder" in metadataset.as_markdown_description
    assert "secret_folder" not in CatalogRecord.from_metadataset(metadataset).abstract


@pytest.mark.parametrize(
    ("registry", "code"),
    [
        ("srs_undefined", "srs_no_epsg"),
        ("EPSG", "srs_no_epsg"),
        ("EPSG", None),
    ],
)
def test_undefined_crs_makes_no_code(registry, code):
    record = CatalogRecord.from_metadataset(
        _vector(crs_registry=registry, crs_registry_code=code)
    )

    assert record.crs_codes == ()


def test_undefined_crs_name_is_not_a_keyword():
    record = CatalogRecord.from_metadataset(
        _vector(crs_name="srs_undefined", crs_registry_code="srs_no_epsg")
    )

    assert record.keywords == ("ESRI Shapefile",)
    assert "srs_undefined" not in record.abstract


def test_missing_format_is_not_a_keyword():
    record = CatalogRecord.from_metadataset(
        _vector(format_gdal_long_name=None, format_gdal_short_name=None)
    )

    assert record.keywords == ("RGF93 v1 / Lambert-93",)
    assert record.formats == ()


def test_flat_database_covers_its_layers():
    metadataset = MetaDatabaseFlat(
        name="base",
        path=Path("base.gpkg"),
        format_gdal_long_name="GeoPackage",
        format_gdal_short_name="GPKG",
        layers=[
            _layer(name="a", bbox_wgs84=(1.0, 2.0, 3.0, 4.0)),
            _layer(
                name="b",
                bbox_wgs84=(0.0, 3.0, 2.0, 5.0),
                crs_name="RGF93 v1 / Lambert-93",
                crs_registry_code="2154",
            ),
            _layer(name="c", bbox_wgs84=None),
        ],
    )

    record = CatalogRecord.from_metadataset(metadataset)

    assert record.bbox_wgs84 == (0.0, 2.0, 3.0, 5.0)
    assert record.crs_codes == ("EPSG:4326", "EPSG:2154")
    assert record.keywords == ("GeoPackage", "GPKG", "WGS 84", "RGF93 v1 / Lambert-93")
    assert "- Layers: 3" in record.abstract
    assert "- a (Point, 3 objects)" in record.abstract


def test_flat_database_without_extent():
    metadataset = MetaDatabaseFlat(name="base", path=Path("base.gpkg"), layers=[])

    assert CatalogRecord.from_metadataset(metadataset).bbox_wgs84 is None


def test_table_is_identified_by_its_location():
    metadataset = MetaDatabaseTable(
        name="public.roads",
        database_connection=DatabaseConnection(
            database_name="db", host="h", port=5432, user_name="alice"
        ),
    )

    record = CatalogRecord.from_metadataset(metadataset)

    assert record.identifier == metadataset.uuid
    assert record.date_created is None


def test_original_path_only_on_demand():
    metadataset = _vector()

    assert CatalogRecord.from_metadataset(metadataset).original_path is None
    assert (
        CatalogRecord.from_metadataset(
            metadataset, CatalogRecordSettings(include_original_path=True)
        ).original_path
        == metadataset.path_as_str
    )


@pytest.mark.parametrize(
    "metadataset",
    [
        MetaDataset(path=Path("parcels.shp")),
        MetaVectorDataset(name="layer_of_a_gpkg"),
    ],
)
def test_unidentifiable_dataset_is_refused(metadataset):
    with pytest.raises(ValueError, match="name and a location"):
        CatalogRecord.from_metadataset(metadataset)


@pytest.mark.parametrize(
    ("language", "expected"),
    [
        ("FR", "fre"),
        (AvailableLocales.french, "fre"),
        ("ES", "spa"),
        ("EN", "eng"),
        (("fr_FR", "UTF-8"), "fre"),
        ((None, None), "eng"),
        (None, "eng"),
        ("xx", "eng"),
    ],
)
def test_settings_language(language, expected):
    assert (
        CatalogRecordSettings.from_environment(language=language).language == expected
    )


def test_settings_from_environment(monkeypatch):
    monkeypatch.setenv("DICOGIS_ISO_CONTACT_ORGANISATION", "Org")
    monkeypatch.setenv("DICOGIS_ISO_CONTACT_EMAIL", "a@example.org")
    monkeypatch.setenv("DICOGIS_ISO_INCLUDE_ORIGINAL_PATH", "true")

    settings = CatalogRecordSettings.from_environment()

    assert settings.contact_organisation == "Org"
    assert settings.contact_email == "a@example.org"
    assert settings.include_original_path is True


def test_settings_explicit_option_wins_over_environment(monkeypatch):
    monkeypatch.setenv("DICOGIS_ISO_INCLUDE_ORIGINAL_PATH", "true")

    settings = CatalogRecordSettings.from_environment(include_original_path=False)

    assert settings.include_original_path is False


def test_settings_defaults(monkeypatch):
    for name in (
        "DICOGIS_ISO_CONTACT_ORGANISATION",
        "DICOGIS_ISO_CONTACT_EMAIL",
        "DICOGIS_ISO_INCLUDE_ORIGINAL_PATH",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = CatalogRecordSettings.from_environment()

    assert settings.contact_organisation is None
    assert settings.contact_email is None
    assert settings.include_original_path is False


# ##############################################################################
# ##### Stand alone program ########
# ##################################
if __name__ == "__main__":
    pytest.main([__file__])
