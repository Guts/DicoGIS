#! python3  # noqa: E265

"""Catalog record: what a metadata catalog gets to know about a dataset.

Pivot between the metadatasets and the catalog formats, and the single list of the
fields managed by DicoGIS: each format serializes it, and completing a record already
in a catalog relies on it too. It holds no absolute path unless asked to: a catalog is
made to be read by people who have no business knowing the local file tree.
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# Standard library
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime
from os import getenv
from typing import Literal

# project
from dicogis.models.metadataset import (
    MetaDatabaseFlat,
    MetaDataset,
    MetaRasterDataset,
    MetaVectorDataset,
)
from dicogis.utils.formatters import convert_octets
from dicogis.utils.str2bool import str2bool
from dicogis.utils.texts import normalize_language_code


# ##############################################################################
# ############ Globals ############
# #################################

logger = logging.getLogger(__name__)

# AvailableLocales value -> ISO 639-2/B code
ISO_639_2_LANGUAGES: dict[str, str] = {"EN": "eng", "ES": "spa", "FR": "fre"}

# what GeoReaderBase.get_srs_details() returns when it can't tell
_UNDEFINED_CRS_VALUES: frozenset[str] = frozenset(
    {"srs_undefined", "srs_no_epsg", "srs_nr"}
)

# ##############################################################################
# ########## Classes ###############
# ##################################


@dataclass(frozen=True)
class CatalogRecordSettings:
    """What a catalog record needs on top of the metadataset.

    Attributes:
        language: language of the record, as an ISO 639-2/B code
        contact_organisation: organisation to contact about the metadata
        contact_email: email address to contact about the metadata
        include_original_path: publish the location of the dataset
    """

    language: str = "eng"
    contact_organisation: str | None = None
    contact_email: str | None = None
    include_original_path: bool = False

    @classmethod
    def from_environment(
        cls,
        language: str | tuple | None = None,
        include_original_path: bool | None = None,
    ) -> CatalogRecordSettings:
        """Build the settings, from the environment for what isn't given.

        Args:
            language: language in any form `normalize_language_code()` understands
            include_original_path: publish the location of the dataset. Defaults to
                the DICOGIS_ISO_INCLUDE_ORIGINAL_PATH environment variable.

        Returns:
            settings
        """
        if include_original_path is None:
            include_original_path = bool(
                str2bool(getenv("DICOGIS_ISO_INCLUDE_ORIGINAL_PATH", "false"))
            )
        return cls(
            language=ISO_639_2_LANGUAGES[normalize_language_code(language)],
            contact_organisation=getenv("DICOGIS_ISO_CONTACT_ORGANISATION") or None,
            contact_email=getenv("DICOGIS_ISO_CONTACT_EMAIL") or None,
            include_original_path=include_original_path,
        )


@dataclass(frozen=True)
class CatalogRecord:
    """A metadata record, independent of the format it ends up in.

    Attributes:
        identifier: stable identifier, see `MetaDataset.uuid`
        title: title of the dataset
        abstract: description of the dataset, never empty
        language: language of the record, as an ISO 639-2/B code
        metadata_date: date of the record itself
        spatial_representation: "vector" or "grid"
        keywords: unique keywords
        date_created: creation date of the dataset, if known
        date_revised: last revision date of the dataset, if known
        bbox_wgs84: (west, south, east, north) in degrees, if known
        crs_codes: unique CRS, as "registry:code"
        formats: names of the formats of the dataset
        contact_organisation: organisation to contact about the metadata
        contact_email: email address to contact about the metadata
        original_path: location of the dataset, only if asked for
    """

    identifier: str
    title: str
    abstract: str
    language: str
    metadata_date: date
    spatial_representation: Literal["vector", "grid"]
    keywords: tuple[str, ...] = ()
    date_created: date | None = None
    date_revised: date | None = None
    bbox_wgs84: tuple[float, float, float, float] | None = None
    crs_codes: tuple[str, ...] = ()
    formats: tuple[str, ...] = ()
    contact_organisation: str | None = None
    contact_email: str | None = None
    original_path: str | None = None

    @classmethod
    def from_metadataset(
        cls,
        metadataset: MetaDataset,
        settings: CatalogRecordSettings | None = None,
    ) -> CatalogRecord:
        """Build the record of a dataset. A flat database makes one record, covering
        all its layers.

        Args:
            metadataset: dataset to describe
            settings: record settings. Defaults to the default ones.

        Raises:
            ValueError: if the dataset has no name or no location to be identified by

        Returns:
            catalog record
        """
        settings = settings or CatalogRecordSettings()
        if not metadataset.name or not metadataset.uuid:
            raise ValueError(
                "A catalog record needs a dataset with a name and a location, got: "
                f"name={metadataset.name!r}, path={metadataset.path!r}."
            )

        crs_sources = _crs_sources(metadataset)
        return cls(
            identifier=metadataset.uuid,
            title=metadataset.name,
            abstract=_abstract(metadataset),
            language=settings.language,
            metadata_date=date.today(),
            spatial_representation=(
                "grid" if isinstance(metadataset, MetaRasterDataset) else "vector"
            ),
            keywords=_unique(
                metadataset.format_gdal_long_name,
                metadataset.format_gdal_short_name,
                *(
                    source.crs_name
                    for source in crs_sources
                    if source.crs_name not in _UNDEFINED_CRS_VALUES
                ),
            ),
            date_created=_as_date(metadataset.storage_date_created),
            date_revised=_as_date(metadataset.storage_date_updated),
            bbox_wgs84=_extent(metadataset),
            crs_codes=_unique(*(_crs_code(source) for source in crs_sources)),
            formats=_unique(metadataset.format_gdal_long_name),
            contact_organisation=settings.contact_organisation,
            contact_email=settings.contact_email,
            original_path=(
                metadataset.path_as_str if settings.include_original_path else None
            ),
        )


# ##############################################################################
# ########## Functions #############
# ##################################


def _unique(*values: str | None) -> tuple[str, ...]:
    """Drop empty values and duplicates, keeping the order.

    Args:
        values: values to filter

    Returns:
        filtered values
    """
    return tuple(dict.fromkeys(value for value in values if value))


def _as_date(value: datetime | date | None) -> date | None:
    """Keep the date of a datetime.

    Args:
        value: datetime, date or None

    Returns:
        date or None
    """
    return value.date() if isinstance(value, datetime) else value


def _crs_sources(metadataset: MetaDataset) -> list[MetaDataset]:
    """List what holds the CRS of a dataset: itself, or the layers of a flat database.

    Args:
        metadataset: dataset to describe

    Returns:
        metadatasets to read the CRS from
    """
    if isinstance(metadataset, MetaDatabaseFlat):
        return list(metadataset.layers or [])
    return [metadataset]


def _crs_code(metadataset: MetaDataset) -> str | None:
    """Build the "registry:code" identifier of a CRS.

    Args:
        metadataset: dataset holding the CRS

    Returns:
        CRS identifier, or None if the dataset has no CRS or no code for it
    """
    registry, code = metadataset.crs_registry, metadataset.crs_registry_code
    if (
        not registry
        or not code
        or registry in _UNDEFINED_CRS_VALUES
        or code in _UNDEFINED_CRS_VALUES
    ):
        return None
    return f"{registry}:{code}"


def _extent(metadataset: MetaDataset) -> tuple[float, float, float, float] | None:
    """Get the extent of a dataset: its own, or the one covering its layers.

    Args:
        metadataset: dataset to describe

    Returns:
        (west, south, east, north), or None if unknown
    """
    if not isinstance(metadataset, MetaDatabaseFlat):
        return metadataset.bbox_wgs84

    extents = [
        layer.bbox_wgs84 for layer in metadataset.layers or [] if layer.bbox_wgs84
    ]
    if not extents:
        return None
    wests, souths, easts, norths = zip(*extents, strict=True)
    return (min(wests), min(souths), max(easts), max(norths))


def _abstract(metadataset: MetaDataset) -> str:
    """Describe a dataset, from its own description if it has any.

    Doesn't reuse `MetaDataset.as_markdown_description`, which lists the absolute paths
    of the dependencies of the dataset.

    Args:
        metadataset: dataset to describe

    Returns:
        description, never empty: an abstract is mandatory in ISO 19115
    """
    if metadataset.description:
        return metadataset.description

    lines: list[str] = []
    if metadataset.format_gdal_long_name:
        lines.append(f"- Format: {metadataset.format_gdal_long_name}")
    if isinstance(metadataset, MetaVectorDataset):
        if metadataset.geometry_type:
            lines.append(f"- Geometry type: {metadataset.geometry_type}")
        if metadataset.features_objects_count:
            lines.append(
                f"- Features objects count: {metadataset.features_objects_count}"
            )
    if metadataset.crs_name and metadataset.crs_name not in _UNDEFINED_CRS_VALUES:
        crs_code = _crs_code(metadataset)
        lines.append(
            f"- Spatial Reference System: {metadataset.crs_name}"
            + (f" ({crs_code})" if crs_code else "")
        )
    if metadataset.storage_size:
        lines.append(f"- Size: {convert_octets(metadataset.storage_size)}")

    if isinstance(metadataset, MetaDatabaseFlat) and metadataset.layers:
        lines.append(f"- Layers: {len(metadataset.layers)}")
        lines.extend(
            f"    - {layer.name} ({layer.geometry_type}, "
            f"{layer.features_objects_count} objects)"
            for layer in metadataset.layers
        )
    elif isinstance(metadataset, MetaVectorDataset) and metadataset.feature_attributes:
        lines.append(f"\n## {metadataset.count_feature_attributes} Feature attributes")
        lines.append(metadataset.as_markdown_feature_attributes)
    elif isinstance(metadataset, MetaRasterDataset):
        lines.append("\n## Image metadata")
        lines.append(metadataset.as_markdown_image_metadata)

    return "\n".join(lines) or metadataset.name
