#! python3  # noqa: E265

"""
    Dataset model

"""

# ############################################################################
# ######### Libraries #############
# #################################

# Standard library
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# package
from dicogis.models.database_connection import DatabaseConnection
from dicogis.models.feature_attributes import AttributeField


# ############################################################################
# ######### Classes #############
# ###############################
@dataclass
class MetaDataset:
    """Dataset abstraction model."""

    name: str | None = None
    path: Path | None = None  # empty if storage_type == database
    parent_folder_name: str | None = None  # empty if storage_type == database
    # format
    format_gdal_long_name: str | None = None
    format_gdal_short_name: str | None = None
    files_dependencies: list[Path] | None = None
    # storage
    storage_date_created: datetime | None = None
    storage_date_updated: datetime | None = None
    storage_size: int | None = None
    storage_type: str | None = None
    # data
    bbox: tuple[float] | None = None
    envelope: tuple[float] | None = None
    crs_name: str | None = None
    crs_registry: str = "EPSG"
    crs_registry_code: str | None = None
    crs_type: str | None = None

    geometry_type: str | None = None
    # properties
    is_3d: bool = False
    # processing
    processing_succeeded: bool | None = None
    processing_error_msg: str | None = ""
    processing_error_type: str | None = ""


@dataclass
class MetaVectorDataset(MetaDataset):
    """Vector dataset abstraction model."""

    attribute_fields_count: int | None = None
    attribute_fields: tuple[AttributeField] | None = None
    features_count: int = 0


@dataclass
class MetaDatabaseTable(MetaVectorDataset):
    """Database table abstraction model."""

    database_connection: DatabaseConnection | None = None
    schema_name: str = "public"


@dataclass
class MetaRasterDataset(MetaDataset):
    """Raster dataset abstraction model."""

    bands_count: int | None = None
    data_type: str | None = None
    columns_count: int | None = None
    rows_count: int | None = None
    pixel_height: int | None = None
    pixel_width: int | None = None
    origin_x: float | None = None
    origin_y: float | None = None
    orientation: float | None = None
    color_space: str | None = None
    compression_rate: int | None = None
