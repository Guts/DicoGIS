#! python3  # noqa: E265

"""ISO 19139 serializer: one XML metadata file per dataset."""

# ##############################################################################
# ########## Libraries #############
# ##################################

# Standard library
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

# 3rd party
from lxml import etree

# project
from dicogis.export.base_serializer import MetadatasetSerializerBase
from dicogis.export.catalog_record import CatalogRecord, CatalogRecordSettings


if TYPE_CHECKING:
    from datetime import date
    from pathlib import Path

    from dicogis.models.metadataset import MetaDataset


# ##############################################################################
# ############ Globals ############
# #################################

logger = logging.getLogger(__name__)

GCO_NS: str = "http://www.isotc211.org/2005/gco"
GMD_NS: str = "http://www.isotc211.org/2005/gmd"
ISO19139_NAMESPACES: dict[str, str] = {"gco": GCO_NS, "gmd": GMD_NS}

_CODELISTS: str = "http://standards.iso.org/iso/19139/resources/gmxCodelists.xml"
_LANGUAGE_CODELIST: str = "http://www.loc.gov/standard/iso639-2/"

_DATA_IDENTIFICATION: str = "gmd:identificationInfo/gmd:MD_DataIdentification"
_CITATION: str = f"{_DATA_IDENTIFICATION}/gmd:citation/gmd:CI_Citation"

# Where each field of the catalog record managed by DicoGIS ends up in a record,
# from its root. Field of CatalogRecord (or group of fields) -> XPath.
ISO19139_FIELDS: dict[str, str] = {
    "contact": "gmd:contact",
    "crs_codes": "gmd:referenceSystemInfo",
    "title": f"{_CITATION}/gmd:title",
    "dates": f"{_CITATION}/gmd:date",
    "abstract": f"{_DATA_IDENTIFICATION}/gmd:abstract",
    "keywords": f"{_DATA_IDENTIFICATION}/gmd:descriptiveKeywords",
    "spatial_representation": f"{_DATA_IDENTIFICATION}/gmd:spatialRepresentationType",
    "language": f"{_DATA_IDENTIFICATION}/gmd:language",
    "bbox_wgs84": f"{_DATA_IDENTIFICATION}/gmd:extent",
    "original_path": f"{_DATA_IDENTIFICATION}/gmd:supplementalInformation",
    "formats": "gmd:distributionInfo/gmd:MD_Distribution/gmd:distributionFormat",
}

# Order of the children of the elements fields are added to, from the XSD
# (schemas.opengis.net/iso/19139/20070417/gmd): a valid record must follow it.
ISO19139_SEQUENCES: dict[str, tuple[str, ...]] = {
    "MD_Metadata": (
        "fileIdentifier",
        "language",
        "characterSet",
        "parentIdentifier",
        "hierarchyLevel",
        "hierarchyLevelName",
        "contact",
        "dateStamp",
        "metadataStandardName",
        "metadataStandardVersion",
        "dataSetURI",
        "locale",
        "spatialRepresentationInfo",
        "referenceSystemInfo",
        "metadataExtensionInfo",
        "identificationInfo",
        "contentInfo",
        "distributionInfo",
        "dataQualityInfo",
        "portrayalCatalogueInfo",
        "metadataConstraints",
        "applicationSchemaInfo",
        "metadataMaintenance",
        "series",
        "describes",
        "propertyType",
        "featureType",
        "featureAttribute",
    ),
    "MD_DataIdentification": (
        "citation",
        "abstract",
        "purpose",
        "credit",
        "status",
        "pointOfContact",
        "resourceMaintenance",
        "graphicOverview",
        "resourceFormat",
        "descriptiveKeywords",
        "resourceSpecificUsage",
        "resourceConstraints",
        "aggregationInfo",
        "spatialRepresentationType",
        "spatialResolution",
        "language",
        "characterSet",
        "topicCategory",
        "environmentDescription",
        "extent",
        "supplementalInformation",
    ),
    "CI_Citation": (
        "title",
        "alternateTitle",
        "date",
        "edition",
        "editionDate",
        "identifier",
        "citedResponsibleParty",
        "presentationForm",
        "series",
        "otherCitationDetails",
        "collectiveTitle",
        "ISBN",
        "ISSN",
    ),
    "MD_Distribution": ("distributionFormat", "distributor", "transferOptions"),
}

# ##############################################################################
# ########## Functions #############
# ##################################


def _gmd(tag: str) -> str:
    return f"{{{GMD_NS}}}{tag}"


def _gco(tag: str) -> str:
    return f"{{{GCO_NS}}}{tag}"


def _add(parent: etree._Element, *tags: str) -> etree._Element:
    """Add nested gmd elements.

    Args:
        parent: element to add to
        tags: names of the elements, each one in the previous one

    Returns:
        deepest element added
    """
    for tag in tags:
        parent = etree.SubElement(parent, _gmd(tag))
    return parent


def _add_text(parent: etree._Element, tag: str, text: str) -> etree._Element:
    """Add a gmd element holding a character string.

    Args:
        parent: element to add to
        tag: name of the element
        text: text to hold

    Returns:
        element added
    """
    element = _add(parent, tag)
    etree.SubElement(element, _gco("CharacterString")).text = text
    return element


def _add_code(
    parent: etree._Element, tag: str, code_type: str, value: str
) -> etree._Element:
    """Add a gmd element holding a value of an ISO 19139 codelist.

    Args:
        parent: element to add to
        tag: name of the element
        code_type: name of the codelist, which is also the one of the code element
        value: value in the codelist

    Returns:
        element added
    """
    element = _add(parent, tag)
    code = _add(element, code_type)
    code.set("codeList", f"{_CODELISTS}#{code_type}")
    code.set("codeListValue", value)
    code.text = value
    return element


def _add_language(parent: etree._Element, language: str) -> None:
    """Add a language: mandatory for the resource, not only for the metadata.

    Args:
        parent: element to add to
        language: ISO 639-2/B code
    """
    code = _add(parent, "language", "LanguageCode")
    code.set("codeList", _LANGUAGE_CODELIST)
    code.set("codeListValue", language)
    code.text = language


def _add_contact(root: etree._Element, record: CatalogRecord) -> None:
    """Add the point of contact of the metadata. Its role alone is enough for the XSD.

    Args:
        root: root of the record
        record: catalog record
    """
    party = _add(root, "contact", "CI_ResponsibleParty")
    if record.contact_organisation:
        _add_text(party, "organisationName", record.contact_organisation)
    if record.contact_email:
        address = _add(party, "contactInfo", "CI_Contact", "address", "CI_Address")
        _add_text(address, "electronicMailAddress", record.contact_email)
    _add_code(party, "role", "CI_RoleCode", "pointOfContact")


def _add_date(citation: etree._Element, value: date, date_type: str) -> None:
    """Add a date of the resource.

    Args:
        citation: citation to add to
        value: date to add
        date_type: value of the CI_DateTypeCode codelist
    """
    ci_date = _add(citation, "date", "CI_Date")
    etree.SubElement(_add(ci_date, "date"), _gco("Date")).text = value.isoformat()
    _add_code(ci_date, "dateType", "CI_DateTypeCode", date_type)


def _add_citation(identification: etree._Element, record: CatalogRecord) -> None:
    """Add the citation of the resource. Its date is mandatory: declared unknown when
    the dataset doesn't tell, typically a database table.

    Args:
        identification: identification section to add to
        record: catalog record
    """
    citation = _add(identification, "citation", "CI_Citation")
    _add_text(citation, "title", record.title)
    if record.date_created:
        _add_date(citation, record.date_created, "creation")
    if record.date_revised:
        _add_date(citation, record.date_revised, "revision")
    if not record.date_created and not record.date_revised:
        _add(citation, "date").set(_gco("nilReason"), "unknown")


def _add_extent(
    identification: etree._Element, bbox: tuple[float, float, float, float]
) -> None:
    """Add the geographic extent of the resource.

    Args:
        identification: identification section to add to
        bbox: (west, south, east, north) in degrees
    """
    west, south, east, north = bbox
    box = _add(
        identification,
        "extent",
        "EX_Extent",
        "geographicElement",
        "EX_GeographicBoundingBox",
    )
    for tag, value in (
        ("westBoundLongitude", west),
        ("eastBoundLongitude", east),
        ("southBoundLatitude", south),
        ("northBoundLatitude", north),
    ):
        etree.SubElement(_add(box, tag), _gco("Decimal")).text = str(value)


def _add_identification(root: etree._Element, record: CatalogRecord) -> None:
    """Add the section describing the resource itself.

    Args:
        root: root of the record
        record: catalog record
    """
    identification = _add(root, "identificationInfo", "MD_DataIdentification")
    _add_citation(identification, record)
    _add_text(identification, "abstract", record.abstract)
    if record.keywords:
        keywords = _add(identification, "descriptiveKeywords", "MD_Keywords")
        for keyword in record.keywords:
            _add_text(keywords, "keyword", keyword)
    _add_code(
        identification,
        "spatialRepresentationType",
        "MD_SpatialRepresentationTypeCode",
        record.spatial_representation,
    )
    _add_language(identification, record.language)
    if record.bbox_wgs84:
        _add_extent(identification, record.bbox_wgs84)
    if record.original_path:
        _add_text(identification, "supplementalInformation", record.original_path)


def record_to_iso19139(record: CatalogRecord) -> etree._Element:
    """Build the ISO 19139 document of a catalog record.

    Args:
        record: catalog record

    Returns:
        root element (gmd:MD_Metadata). Its children and the ones of the elements in
        ISO19139_SEQUENCES come in the order of the XSD.
    """
    root = etree.Element(_gmd("MD_Metadata"), nsmap=ISO19139_NAMESPACES)
    _add_text(root, "fileIdentifier", record.identifier)
    _add_language(root, record.language)
    _add_code(root, "characterSet", "MD_CharacterSetCode", "utf8")
    _add_code(root, "hierarchyLevel", "MD_ScopeCode", "dataset")
    _add_contact(root, record)
    date_stamp = _add(root, "dateStamp")
    etree.SubElement(date_stamp, _gco("Date")).text = record.metadata_date.isoformat()
    _add_text(root, "metadataStandardName", "ISO 19115:2003/19139")
    _add_text(root, "metadataStandardVersion", "1.0")
    for crs_code in record.crs_codes:
        identifier = _add(
            root,
            "referenceSystemInfo",
            "MD_ReferenceSystem",
            "referenceSystemIdentifier",
            "RS_Identifier",
        )
        _add_text(identifier, "code", crs_code)
    _add_identification(root, record)
    if record.formats:
        distribution = _add(root, "distributionInfo", "MD_Distribution")
        for format_name in record.formats:
            md_format = _add(distribution, "distributionFormat", "MD_Format")
            _add_text(md_format, "name", format_name)
            # mandatory, and GDAL doesn't tell the version of a format
            _add(md_format, "version").set(_gco("nilReason"), "unknown")
    return root


# ##############################################################################
# ########## Classes ###############
# ##################################


class MetadatasetSerializerIso19139(MetadatasetSerializerBase):
    """Export to ISO 19139 XML files."""

    def __init__(
        self,
        # custom
        settings: CatalogRecordSettings | None = None,
        # inherited
        localized_strings: dict | None = None,
        output_path: Path | None = None,
        opt_size_prettify: bool = True,
    ) -> None:
        """Store metadata into ISO 19139 XML files.

        Args:
            settings: settings of the records. Defaults to the ones of the environment.
            localized_strings: localized texts
            output_path: folder where to write the files, created if needed
            opt_size_prettify: option to prettify size in octets

        Raises:
            ValueError: if output_path is not set
        """
        if output_path is None:
            raise ValueError(
                "output_path is required to serialize metadatasets as ISO 19139 files."
            )
        output_path.mkdir(parents=True, exist_ok=True)
        self.settings = settings or CatalogRecordSettings.from_environment()
        if not self.settings.contact_organisation and not self.settings.contact_email:
            logger.warning(
                "No contact set for the metadata records: gmd:contact only holds its "
                "role. Set DICOGIS_ISO_CONTACT_ORGANISATION and "
                "DICOGIS_ISO_CONTACT_EMAIL to fill it."
            )

        super().__init__(
            localized_strings=localized_strings,
            opt_size_prettify=opt_size_prettify,
            output_path=output_path,
        )

    def serialize_metadaset(self, metadataset: MetaDataset) -> Path | None:
        """Serialize input metadataset as an XML file stored in output_path.

        A dataset that couldn't even be opened makes no record: it would have nothing
        to tell a catalog. Not based on `processing_succeeded`, which is also False for
        a readable dataset, because of an empty layer of a database for example.

        Args:
            metadataset: metadataset to serialize

        Returns:
            path to the generated file, or None if the dataset couldn't be read
        """
        if metadataset.format_gdal_short_name is None:
            logger.warning(
                f"Dataset {metadataset.name} couldn't be read: no ISO 19139 record for "
                f"it. Trace: {metadataset.processing_error_msg}"
            )
            return None

        root = record_to_iso19139(
            CatalogRecord.from_metadataset(metadataset, self.settings)
        )
        output_filepath = self.output_path.joinpath(
            self.unique_output_filename(metadataset.name, ".xml")
        )
        etree.ElementTree(root).write(
            str(output_filepath),
            encoding="UTF-8",
            xml_declaration=True,
            pretty_print=True,
        )
        logger.debug(
            f"Metadataset {metadataset.name} serialized into ISO 19139 file "
            f"{output_filepath}"
        )
        return output_filepath
