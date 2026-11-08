#! python3  # noqa: E265

"""
Tests for dicogis.export.to_iso19139.

Checks the mandatory elements and the order of the XSD against the tables of the
serializer: the real validation against the XSD happens in a GeoNetwork instance (see
tests/container and the rejectIfInvalid scenario of the integration workflow).

Usage from the repo root folder:
    pytest tests/test_export_iso19139.py
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# standard library
import logging
from datetime import date, datetime
from pathlib import Path

# 3rd party
import pytest
from lxml import etree
from typer.testing import CliRunner

# project
from dicogis.cli.main import dicogis_cli
from dicogis.export.base_serializer import MetadatasetSerializerBase
from dicogis.export.catalog_record import CatalogRecord, CatalogRecordSettings
from dicogis.export.to_iso19139 import (
    GCO_NS,
    ISO19139_FIELDS,
    ISO19139_NAMESPACES,
    ISO19139_SEQUENCES,
    MetadatasetSerializerIso19139,
    record_to_iso19139,
)
from dicogis.georeaders.read_raster import ReadRasters
from dicogis.georeaders.read_vector_flat_dataset import ReadVectorFlatDataset
from dicogis.models.database_connection import DatabaseConnection
from dicogis.models.metadataset import (
    MetaDatabaseFlat,
    MetaDatabaseTable,
    MetaVectorDataset,
)


# ##############################################################################
# ########## Globals ###############
# ##################################

GISDATA = Path(__file__).parent / "fixtures" / "gisdata" / "data" / "good"
IDENT = "gmd:identificationInfo/gmd:MD_DataIdentification"

# ##############################################################################
# ########## Functions #############
# ##################################


def _record(**overrides) -> CatalogRecord:
    values = dict(
        identifier="6a4e5ba7-e7dd-533a-a57c-42632717ecfe",
        title="parcels",
        abstract="Land parcels.",
        language="fre",
        metadata_date=date(2026, 11, 8),
        spatial_representation="vector",
        keywords=("ESRI Shapefile", "WGS 84"),
        date_created=date(2020, 1, 2),
        date_revised=date(2021, 3, 4),
        bbox_wgs84=(2.0, 48.0, 3.0, 49.0),
        crs_codes=("EPSG:4326",),
        formats=("ESRI Shapefile",),
        contact_organisation="Org",
        contact_email="a@example.org",
    )
    values.update(overrides)
    return CatalogRecord(**values)


def _text(root: etree._Element, xpath: str) -> str | None:
    found = root.findall(xpath, ISO19139_NAMESPACES)
    return found[0].text if found else None


def _all_text(root: etree._Element, xpath: str) -> list[str]:
    return [node.text for node in root.findall(xpath, ISO19139_NAMESPACES)]


def _assert_follows_xsd_order(root: etree._Element) -> None:
    for parent in root.iter():
        sequence = ISO19139_SEQUENCES.get(etree.QName(parent).localname)
        if sequence is None:
            continue
        ranks = [sequence.index(etree.QName(child).localname) for child in parent]
        assert ranks == sorted(ranks), etree.QName(parent).localname


@pytest.fixture
def serializer(tmp_path: Path) -> MetadatasetSerializerIso19139:
    return MetadatasetSerializerIso19139(
        settings=CatalogRecordSettings(language="eng"),
        localized_strings={},
        output_path=tmp_path,
    )


# ##############################################################################
# ########## Document tests #########
# ##################################


def test_document_content():
    root = record_to_iso19139(_record())

    assert etree.QName(root).localname == "MD_Metadata"
    assert _text(root, "gmd:fileIdentifier/gco:CharacterString") == (
        "6a4e5ba7-e7dd-533a-a57c-42632717ecfe"
    )
    assert _text(root, "gmd:language/gmd:LanguageCode") == "fre"
    assert _text(root, "gmd:characterSet/gmd:MD_CharacterSetCode") == "utf8"
    assert _text(root, "gmd:hierarchyLevel/gmd:MD_ScopeCode") == "dataset"
    assert _text(root, "gmd:dateStamp/gco:Date") == "2026-11-08"
    assert (
        _text(
            root,
            "gmd:referenceSystemInfo/gmd:MD_ReferenceSystem"
            "/gmd:referenceSystemIdentifier/gmd:RS_Identifier/gmd:code"
            "/gco:CharacterString",
        )
        == "EPSG:4326"
    )
    assert (
        _text(
            root,
            f"{IDENT}/gmd:citation/gmd:CI_Citation/gmd:title/gco:CharacterString",
        )
        == "parcels"
    )
    assert _text(root, f"{IDENT}/gmd:abstract/gco:CharacterString") == "Land parcels."
    assert _all_text(
        root,
        f"{IDENT}/gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:keyword"
        "/gco:CharacterString",
    ) == ["ESRI Shapefile", "WGS 84"]
    assert (
        _text(
            root,
            f"{IDENT}/gmd:spatialRepresentationType"
            "/gmd:MD_SpatialRepresentationTypeCode",
        )
        == "vector"
    )


def test_resource_language_is_there():
    """Mandatory in MD_DataIdentification, on top of the metadata's one."""
    root = record_to_iso19139(_record())

    assert _text(root, f"{IDENT}/gmd:language/gmd:LanguageCode") == "fre"


def test_codelists_are_declared():
    root = record_to_iso19139(_record())

    code = root.find("gmd:hierarchyLevel/gmd:MD_ScopeCode", ISO19139_NAMESPACES)

    assert code.get("codeListValue") == "dataset"
    assert code.get("codeList").endswith("#MD_ScopeCode")


def test_dates():
    root = record_to_iso19139(_record())

    dates = root.findall(
        f"{IDENT}/gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date",
        ISO19139_NAMESPACES,
    )

    assert [
        (
            _text(ci_date, "gmd:date/gco:Date"),
            _text(ci_date, "gmd:dateType/gmd:CI_DateTypeCode"),
        )
        for ci_date in dates
    ] == [("2020-01-02", "creation"), ("2021-03-04", "revision")]


def test_unknown_dates_are_declared_as_such():
    """A date is mandatory in a citation, and a database table has none."""
    root = record_to_iso19139(_record(date_created=None, date_revised=None))

    citation_date = root.find(
        f"{IDENT}/gmd:citation/gmd:CI_Citation/gmd:date", ISO19139_NAMESPACES
    )

    assert citation_date.get(f"{{{GCO_NS}}}nilReason") == "unknown"
    assert len(citation_date) == 0


def test_extent_is_in_the_order_of_the_xsd():
    root = record_to_iso19139(_record(bbox_wgs84=(1.5, 2.5, 3.5, 4.5)))

    box = root.find(
        f"{IDENT}/gmd:extent/gmd:EX_Extent/gmd:geographicElement"
        "/gmd:EX_GeographicBoundingBox",
        ISO19139_NAMESPACES,
    )

    assert [(etree.QName(bound).localname, bound[0].text) for bound in box] == [
        ("westBoundLongitude", "1.5"),
        ("eastBoundLongitude", "3.5"),
        ("southBoundLatitude", "2.5"),
        ("northBoundLatitude", "4.5"),
    ]


def test_format_version_is_declared_unknown():
    """The version of a format is mandatory, GDAL doesn't tell it."""
    root = record_to_iso19139(_record())

    md_format = root.find(
        "gmd:distributionInfo/gmd:MD_Distribution/gmd:distributionFormat/gmd:MD_Format",
        ISO19139_NAMESPACES,
    )

    assert _text(md_format, "gmd:name/gco:CharacterString") == "ESRI Shapefile"
    assert md_format.find("gmd:version", ISO19139_NAMESPACES).get(
        f"{{{GCO_NS}}}nilReason"
    ) == ("unknown")


def test_contact():
    root = record_to_iso19139(_record())

    party = "gmd:contact/gmd:CI_ResponsibleParty"

    assert _text(root, f"{party}/gmd:organisationName/gco:CharacterString") == "Org"
    assert (
        _text(
            root,
            f"{party}/gmd:contactInfo/gmd:CI_Contact/gmd:address/gmd:CI_Address"
            "/gmd:electronicMailAddress/gco:CharacterString",
        )
        == "a@example.org"
    )
    assert _text(root, f"{party}/gmd:role/gmd:CI_RoleCode") == "pointOfContact"


def test_contact_without_value_only_holds_its_role():
    root = record_to_iso19139(_record(contact_organisation=None, contact_email=None))

    party = root.find("gmd:contact/gmd:CI_ResponsibleParty", ISO19139_NAMESPACES)

    assert [etree.QName(child).localname for child in party] == ["role"]


def test_original_path_only_when_given():
    assert (
        record_to_iso19139(_record()).find(
            f"{IDENT}/gmd:supplementalInformation", ISO19139_NAMESPACES
        )
        is None
    )
    assert (
        _text(
            record_to_iso19139(_record(original_path="/data/parcels.shp")),
            f"{IDENT}/gmd:supplementalInformation/gco:CharacterString",
        )
        == "/data/parcels.shp"
    )


@pytest.mark.parametrize(
    "overrides",
    [
        {},
        {"original_path": "/data/parcels.shp"},
        {"date_created": None, "date_revised": None},
        {
            "bbox_wgs84": None,
            "crs_codes": (),
            "formats": (),
            "keywords": (),
            "contact_email": None,
        },
        {"crs_codes": ("EPSG:4326", "EPSG:2154"), "formats": ("A", "B")},
    ],
)
def test_children_follow_the_order_of_the_xsd(overrides):
    _assert_follows_xsd_order(record_to_iso19139(_record(**overrides)))


def test_mandatory_elements_are_always_there():
    root = record_to_iso19139(
        _record(
            keywords=(),
            date_created=None,
            date_revised=None,
            bbox_wgs84=None,
            crs_codes=(),
            formats=(),
            contact_organisation=None,
            contact_email=None,
        )
    )

    for xpath in (
        "gmd:contact",
        "gmd:dateStamp",
        "gmd:identificationInfo",
        f"{IDENT}/gmd:citation/gmd:CI_Citation/gmd:title",
        f"{IDENT}/gmd:citation/gmd:CI_Citation/gmd:date",
        f"{IDENT}/gmd:abstract",
        f"{IDENT}/gmd:language",
    ):
        assert root.find(xpath, ISO19139_NAMESPACES) is not None, xpath


def test_fields_table_points_at_what_is_generated():
    root = record_to_iso19139(_record(original_path="/data/parcels.shp"))

    for field, xpath in ISO19139_FIELDS.items():
        assert root.find(xpath, ISO19139_NAMESPACES) is not None, field


# ##############################################################################
# ########## Serializer tests #######
# ##################################


def test_factory_builds_the_serializer_from_its_parameters(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("DICOGIS_ISO_CONTACT_EMAIL", "a@example.org")

    serializer = MetadatasetSerializerBase.get_serializer_from_parameters(
        format_or_serializer="iso19139",
        localized_strings={},
        output_path=tmp_path,
        language="FR",
        opt_include_original_path=True,
    )

    assert isinstance(serializer, MetadatasetSerializerIso19139)
    assert serializer.settings.language == "fre"
    assert serializer.settings.include_original_path is True
    assert serializer.settings.contact_email == "a@example.org"


def test_cli_inventory_writes_iso19139_files(tmp_path: Path):
    source_folder = tmp_path / "private_folder"
    source_folder.mkdir()
    for extension in ("shp", "shx", "dbf", "prj"):
        name = f"san_andres_y_providencia_coastline.{extension}"
        (source_folder / name).write_bytes((GISDATA / "vector" / name).read_bytes())
    output_folder = tmp_path / "output"

    result = CliRunner().invoke(
        dicogis_cli,
        [
            "inventory",
            "--input-folder",
            str(source_folder),
            "--formats",
            "esri_shapefile",
            "--output-format",
            "iso19139",
            "--output-path",
            str(output_folder),
            "--language",
            "FR",
            "--no-opt-open-output",
            "--no-opt-notify-sound",
        ],
    )

    assert result.exit_code == 0, result.output
    output_files = list(output_folder.glob("*.xml"))
    assert [output_file.name for output_file in output_files] == [
        "san_andres_y_providencia_coastline.xml"
    ]
    root = etree.parse(str(output_files[0])).getroot()
    assert _text(root, "gmd:language/gmd:LanguageCode") == "fre"
    assert str(source_folder.name) not in etree.tostring(root, encoding="unicode")


def test_output_path_is_required():
    with pytest.raises(ValueError, match="output_path"):
        MetadatasetSerializerIso19139(localized_strings={})


def test_output_folder_is_created(tmp_path: Path):
    output_path = tmp_path / "nested" / "output"

    MetadatasetSerializerIso19139(
        settings=CatalogRecordSettings(), localized_strings={}, output_path=output_path
    )

    assert output_path.is_dir()


def test_serialize_a_real_vector_dataset(serializer):
    metadataset = ReadVectorFlatDataset().infos_dataset(
        source_path=GISDATA / "vector/san_andres_y_providencia_coastline.shp"
    )

    output_file = serializer.serialize_metadaset(metadataset)

    root = etree.parse(str(output_file)).getroot()
    assert output_file.name == "san_andres_y_providencia_coastline.xml"
    assert _text(root, "gmd:fileIdentifier/gco:CharacterString") == metadataset.uuid
    west = _text(
        root,
        f"{IDENT}/gmd:extent/gmd:EX_Extent/gmd:geographicElement"
        "/gmd:EX_GeographicBoundingBox/gmd:westBoundLongitude/gco:Decimal",
    )
    assert float(west) == pytest.approx(-81.3963, abs=1e-4)
    _assert_follows_xsd_order(root)


def test_serialize_a_real_raster_dataset(serializer):
    metadataset = ReadRasters().infos_dataset(
        source_path=GISDATA / "raster/relief_san_andres.tif"
    )

    root = etree.parse(str(serializer.serialize_metadaset(metadataset))).getroot()

    assert (
        _text(
            root,
            f"{IDENT}/gmd:spatialRepresentationType"
            "/gmd:MD_SpatialRepresentationTypeCode",
        )
        == "grid"
    )
    _assert_follows_xsd_order(root)


def test_serialize_a_postgis_table(serializer):
    metadataset = MetaDatabaseTable(
        name="public.roads",
        format_gdal_long_name="PostgreSQL/PostGIS",
        format_gdal_short_name="PostgreSQL",
        database_connection=DatabaseConnection(
            database_name="db", host="h", port=5432, user_name="alice"
        ),
        crs_name="WGS 84",
        crs_registry="EPSG",
        crs_registry_code="4326",
        bbox_wgs84=(1.0, 2.0, 3.0, 4.0),
    )

    root = etree.parse(str(serializer.serialize_metadaset(metadataset))).getroot()

    assert _text(root, "gmd:fileIdentifier/gco:CharacterString") == metadataset.uuid
    assert "alice" not in etree.tostring(root, encoding="unicode")
    _assert_follows_xsd_order(root)


def test_serialize_a_flat_database(serializer):
    metadataset = MetaDatabaseFlat(
        name="base",
        path=Path("base.gpkg"),
        format_gdal_long_name="GeoPackage",
        format_gdal_short_name="GPKG",
        layers=[
            MetaVectorDataset(
                name="a",
                dataset_type="data_layer",
                crs_name="WGS 84",
                crs_registry="EPSG",
                crs_registry_code="4326",
                bbox_wgs84=(1.0, 2.0, 3.0, 4.0),
            )
        ],
        # a readable database with an empty layer is flagged as failed
        processing_succeeded=False,
    )

    output_file = serializer.serialize_metadaset(metadataset)

    assert output_file.name == "base.xml"


def test_serialize_a_dataset_without_crs(serializer):
    metadataset = MetaVectorDataset(
        name="no_crs",
        path=Path("no_crs.shp"),
        format_gdal_long_name="ESRI Shapefile",
        format_gdal_short_name="ESRI Shapefile",
        crs_name="srs_undefined",
        crs_registry="srs_undefined",
        crs_registry_code="srs_no_epsg",
        crs_type="srs_nr",
    )

    root = etree.parse(str(serializer.serialize_metadaset(metadataset))).getroot()

    assert root.find("gmd:referenceSystemInfo", ISO19139_NAMESPACES) is None
    assert root.find(f"{IDENT}/gmd:extent", ISO19139_NAMESPACES) is None
    assert "srs_" not in etree.tostring(root, encoding="unicode")


def test_homonyms_get_their_own_file(serializer):
    first = serializer.serialize_metadaset(
        MetaVectorDataset(
            name="lines", path=Path("a/lines.shp"), format_gdal_short_name="x"
        )
    )
    second = serializer.serialize_metadaset(
        MetaVectorDataset(
            name="lines", path=Path("b/lines.shp"), format_gdal_short_name="x"
        )
    )

    assert (first.name, second.name) == ("lines.xml", "lines-2.xml")


def test_dataset_that_could_not_be_read_makes_no_file(serializer, tmp_path, caplog):
    metadataset = MetaVectorDataset(
        name="corrupted",
        path=Path("corrupted.shp"),
        processing_succeeded=False,
        processing_error_msg="boom",
    )

    with caplog.at_level(logging.WARNING):
        assert serializer.serialize_metadaset(metadataset) is None

    assert not list(tmp_path.iterdir())
    assert "boom" in caplog.text


def test_path_stays_out_of_the_file_by_default(serializer):
    metadataset = MetaVectorDataset(
        name="parcels",
        path=Path("secret_folder/parcels.shp"),
        format_gdal_short_name="x",
        files_dependencies=[Path("secret_folder/parcels.dbf")],
    )

    output_file = serializer.serialize_metadaset(metadataset)

    assert "secret_folder" not in output_file.read_text(encoding="UTF-8")


def test_path_in_the_file_on_demand(tmp_path: Path):
    serializer = MetadatasetSerializerIso19139(
        settings=CatalogRecordSettings(include_original_path=True),
        localized_strings={},
        output_path=tmp_path,
    )
    metadataset = MetaVectorDataset(
        name="parcels",
        path=Path("visible_folder/parcels.shp"),
        format_gdal_short_name="x",
    )

    output_file = serializer.serialize_metadaset(metadataset)

    assert "visible_folder" in output_file.read_text(encoding="UTF-8")


def test_missing_contact_is_logged(tmp_path: Path, caplog):
    with caplog.at_level(logging.WARNING):
        MetadatasetSerializerIso19139(
            settings=CatalogRecordSettings(),
            localized_strings={},
            output_path=tmp_path,
        )

    assert "DICOGIS_ISO_CONTACT_ORGANISATION" in caplog.text


def test_contact_set_is_not_logged(tmp_path: Path, caplog):
    with caplog.at_level(logging.WARNING):
        MetadatasetSerializerIso19139(
            settings=CatalogRecordSettings(contact_email="a@example.org"),
            localized_strings={},
            output_path=tmp_path,
        )

    assert "DICOGIS_ISO_CONTACT_ORGANISATION" not in caplog.text


def test_dates_of_a_real_dataset_are_dates_not_datetimes(serializer):
    metadataset = MetaVectorDataset(
        name="parcels",
        path=Path("parcels.shp"),
        format_gdal_short_name="x",
        storage_date_created=datetime(2020, 1, 2, 3, 4, 5),
    )

    root = etree.parse(str(serializer.serialize_metadaset(metadataset))).getroot()

    assert (
        _text(
            root,
            f"{IDENT}/gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date/gmd:date"
            "/gco:Date",
        )
        == "2020-01-02"
    )


# ##############################################################################
# ##### Stand alone program ########
# ##################################
if __name__ == "__main__":
    pytest.main([__file__])
