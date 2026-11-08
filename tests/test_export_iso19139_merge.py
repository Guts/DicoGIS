#! python3  # noqa: E265

"""
Tests for dicogis.export.to_iso19139.complete_record().

Usage from the repo root folder:
    pytest tests/test_export_iso19139_merge.py
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# standard library
from datetime import date

# 3rd party
import pytest
from lxml import etree

# project
from dicogis.export.catalog_record import CatalogRecord
from dicogis.export.to_iso19139 import (
    ISO19139_NAMESPACES,
    ISO19139_SEQUENCES,
    complete_record,
    record_to_iso19139,
)


# ##############################################################################
# ########## Globals ###############
# ##################################

IDENT = "gmd:identificationInfo/gmd:MD_DataIdentification"
CITATION = f"{IDENT}/gmd:citation/gmd:CI_Citation"
NAMESPACES = (
    'xmlns:gmd="http://www.isotc211.org/2005/gmd" '
    'xmlns:gco="http://www.isotc211.org/2005/gco" '
    'xmlns:gmx="http://www.isotc211.org/2005/gmx" '
    'xmlns:xlink="http://www.w3.org/1999/xlink"'
)

# ##############################################################################
# ########## Functions #############
# ##################################


def _local() -> etree._Element:
    return record_to_iso19139(
        CatalogRecord(
            identifier="id",
            title="local title",
            abstract="local abstract",
            language="fre",
            metadata_date=date(2026, 11, 8),
            spatial_representation="vector",
            keywords=("local keyword",),
            date_created=date(2020, 1, 2),
            bbox_wgs84=(1.0, 2.0, 3.0, 4.0),
            crs_codes=("EPSG:4326",),
            formats=("GeoPackage",),
            contact_organisation="Local org",
        )
    )


def _remote(identification: str = "", root_content: str = "") -> etree._Element:
    """Build a record holding only a title and what's given."""
    return etree.fromstring(
        f"""<gmd:MD_Metadata {NAMESPACES}>
        <gmd:fileIdentifier><gco:CharacterString>id</gco:CharacterString></gmd:fileIdentifier>
        {root_content}
        <gmd:identificationInfo><gmd:MD_DataIdentification>
            <gmd:citation><gmd:CI_Citation>
                <gmd:title><gco:CharacterString>remote title</gco:CharacterString></gmd:title>
            </gmd:CI_Citation></gmd:citation>
            {identification}
        </gmd:MD_DataIdentification></gmd:identificationInfo>
        </gmd:MD_Metadata>"""
    )


def _text(root: etree._Element, xpath: str) -> str | None:
    return root.findtext(xpath, namespaces=ISO19139_NAMESPACES)


def _names(element: etree._Element) -> list[str]:
    return [etree.QName(child).localname for child in element]


# ##############################################################################
# ########## Tests ##################
# ##################################


def test_empty_fields_are_filled():
    completed, added = complete_record(_remote(), _local())

    assert _text(completed, f"{IDENT}/gmd:abstract/gco:CharacterString") == (
        "local abstract"
    )
    assert set(added) == {
        "contact",
        "crs_codes",
        "dates",
        "abstract",
        "keywords",
        "spatial_representation",
        "language",
        "bbox_wgs84",
        "formats",
    }


def test_filled_fields_are_left_as_is():
    completed, added = complete_record(_remote(), _local())

    assert _text(completed, f"{CITATION}/gmd:title/gco:CharacterString") == (
        "remote title"
    )
    assert "title" not in added


def test_what_dicogis_does_not_manage_is_left_as_is():
    remote = _remote(
        identification="""<gmd:purpose>
            <gco:CharacterString>handmade purpose</gco:CharacterString>
        </gmd:purpose>"""
    )

    completed, _added = complete_record(remote, _local())

    assert _text(completed, f"{IDENT}/gmd:purpose/gco:CharacterString") == (
        "handmade purpose"
    )


def test_added_elements_follow_the_order_of_the_xsd():
    remote = _remote(
        identification="""
        <gmd:purpose><gco:CharacterString>p</gco:CharacterString></gmd:purpose>
        <gmd:topicCategory>
            <gmd:MD_TopicCategoryCode>farming</gmd:MD_TopicCategoryCode>
        </gmd:topicCategory>"""
    )

    completed, _added = complete_record(remote, _local())

    identification = completed.find(IDENT, ISO19139_NAMESPACES)
    assert _names(identification) == [
        "citation",
        "abstract",
        "purpose",
        "descriptiveKeywords",
        "spatialRepresentationType",
        "language",
        "topicCategory",
        "extent",
    ]
    assert _names(completed) == [
        "fileIdentifier",
        "contact",
        "referenceSystemInfo",
        "identificationInfo",
        "distributionInfo",
    ]
    for parent in completed.iter(etree.Element):
        sequence = ISO19139_SEQUENCES.get(etree.QName(parent).localname)
        if sequence:
            ranks = [sequence.index(name) for name in _names(parent)]
            assert ranks == sorted(ranks)


@pytest.mark.parametrize(
    "empty_abstract",
    [
        "<gmd:abstract/>",
        '<gmd:abstract gco:nilReason="missing"/>',
        "<gmd:abstract><gco:CharacterString/></gmd:abstract>",
        "<gmd:abstract><gco:CharacterString>   </gco:CharacterString></gmd:abstract>",
    ],
)
def test_empty_element_is_replaced_not_duplicated(empty_abstract):
    completed, added = complete_record(_remote(identification=empty_abstract), _local())

    abstracts = completed.findall(f"{IDENT}/gmd:abstract", ISO19139_NAMESPACES)
    assert len(abstracts) == 1
    assert abstracts[0].findtext("gco:CharacterString", namespaces=ISO19139_NAMESPACES)
    assert "abstract" in added


@pytest.mark.parametrize(
    "filled_abstract",
    [
        "<gmd:abstract><gco:CharacterString>remote</gco:CharacterString></gmd:abstract>",
        '<gmd:abstract><gmx:Anchor xlink:href="http://a">remote</gmx:Anchor></gmd:abstract>',
        """<gmd:abstract><gmd:PT_FreeText><gmd:textGroup>
            <gmd:LocalisedCharacterString locale="#FR">remote</gmd:LocalisedCharacterString>
        </gmd:textGroup></gmd:PT_FreeText></gmd:abstract>""",
    ],
)
def test_every_way_of_filling_a_field_is_recognized(filled_abstract):
    completed, added = complete_record(
        _remote(identification=filled_abstract), _local()
    )

    assert "abstract" not in added
    assert "local abstract" not in etree.tostring(completed, encoding="unicode")


def test_codelist_value_without_text_counts_as_filled():
    remote = _remote(
        identification="""<gmd:spatialRepresentationType>
            <gmd:MD_SpatialRepresentationTypeCode codeList="x" codeListValue="grid"/>
        </gmd:spatialRepresentationType>"""
    )

    _completed, added = complete_record(remote, _local())

    assert "spatial_representation" not in added


def test_reference_to_another_record_counts_as_filled():
    remote = _remote(root_content='<gmd:contact xlink:href="http://a/contact"/>')

    _completed, added = complete_record(remote, _local())

    assert "contact" not in added


def test_nothing_to_add_returns_no_field():
    local = _local()

    _completed, added = complete_record(_local(), local)

    assert added == []


def test_local_empty_value_is_not_added():
    """A date declared unknown has nothing to teach to a catalog."""
    local = record_to_iso19139(
        CatalogRecord(
            identifier="id",
            title="t",
            abstract="a",
            language="fre",
            metadata_date=date(2026, 11, 8),
            spatial_representation="vector",
        )
    )

    completed, added = complete_record(_remote(), local)

    assert "dates" not in added
    assert completed.find(f"{CITATION}/gmd:date", ISO19139_NAMESPACES) is None


def test_comment_in_the_record_is_harmless():
    remote = _remote(root_content="<!-- a comment -->")

    _completed, added = complete_record(remote, _local())

    assert "contact" in added


def test_service_record_gets_no_data_description():
    remote = etree.fromstring(
        f"""<gmd:MD_Metadata {NAMESPACES}>
        <gmd:identificationInfo>
            <srv:SV_ServiceIdentification xmlns:srv="http://www.isotc211.org/2005/srv"/>
        </gmd:identificationInfo>
        </gmd:MD_Metadata>"""
    )

    completed, added = complete_record(remote, _local())

    assert completed.find(IDENT, ISO19139_NAMESPACES) is None
    assert "abstract" not in added
    assert "contact" in added


def test_other_schema_is_refused():
    remote = etree.fromstring(
        '<mdb:MD_Metadata xmlns:mdb="http://standards.iso.org/iso/19115/-3/mdb/2.0"/>'
    )

    with pytest.raises(ValueError, match="Not an ISO 19139 record"):
        complete_record(remote, _local())


# ##############################################################################
# ##### Stand alone program ########
# ##################################
if __name__ == "__main__":
    pytest.main([__file__])
