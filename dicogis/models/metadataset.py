#! python3  # noqa: E265

"""Metadaset models."""

# ############################################################################
# ######### Libraries #############
# #################################

# Standard library
import logging
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Literal

# package
from dicogis.models.database_connection import DatabaseConnection
from dicogis.models.feature_attributes import AttributeField
from dicogis.utils.formatters import convert_octets
from dicogis.utils.slugger import sluggy

# ############################################################################
# ########## Globals ###############
# ##################################


logger = logging.getLogger(__name__)


# ############################################################################
# ######### Classes #############
# ###############################


@dataclass
class MetaDataset:
    """Dataset abstraction model."""

    name: str | None = None
    path: Path | None = None  # empty if storage_type == database
    parent_folder_name: str | None = None  # empty if storage_type == database
    dataset_type: (
        None
        | Literal[
            "flat_cad",
            "flat_database",
            "flat_database_esri",
            "flat_raster",
            "flat_vector",
            "sgbd_postgis",
        ]
    ) = None
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

    # related objects

    # properties
    is_3d: bool = False
    # processing
    processing_succeeded: bool | None = None
    processing_error_msg: str | None = ""
    processing_error_type: str | None = ""

    @property
    def as_markdown_description(self) -> str:
        """Concatenate some informations as a markdown description.

        Returns:
            markdown description of the metadataset
        """
        description = f"- Dataset type: {self.dataset_type}\n"

        if self.format_gdal_long_name:
            description += f"- Format: {self.format_gdal_long_name}\n"

        if isinstance(self, MetaVectorDataset) and self.geometry_type:
            description += f"- Geometry type: {self.geometry_type}\n"

        if isinstance(self, MetaVectorDataset) and self.features_objects_count:
            description += f"- Features objects count: {self.features_objects_count}\n"

        if (
            (self.crs_name and self.crs_name != "srs_undefined")
            or self.crs_registry
            or self.crs_registry_code
            or self.crs_type
        ):
            description += (
                f"- Spatial Reference System: {self.crs_name} {self.crs_type}\n"
            )
            if self.crs_registry_code:
                description += f"{self.crs_registry}:{self.crs_registry_code}\n"
            else:
                description += "\n"

        if self.storage_size:
            description += f"- Size: {convert_octets(self.storage_size)}\n"

        if self.files_dependencies:
            description += (
                "- Related files: "
                + f"{', '.join([str(filepath.resolve()) for filepath  in self.files_dependencies])}\n"
            )

        if isinstance(self, MetaVectorDataset) and self.feature_attributes:
            description += (
                f"\n\n## {self.count_feature_attributes} Feature attributes\n"
            )
            description += self.as_markdown_feature_attributes
        elif isinstance(self, MetaRasterDataset):
            description += "\n\n### Image metadata\n"
            description += self.as_markdown_image_metadata

        return description

    @property
    def path_as_str(self) -> str | None:
        """Helper to have an universal path resolver independent of source type.

        Returns:
            str | None: path or connection uri (without password)
        """
        if isinstance(self.path, Path):
            return f"{self.path.resolve()}"
        elif isinstance(self, MetaDatabaseTable) and isinstance(
            self.database_connection, DatabaseConnection
        ):
            if self.database_connection.service_name is not None:
                out_connection_string = (
                    self.database_connection.pg_connection_uri.split(
                        "&application_name="
                    )[0]
                )
            else:
                out_connection_string = (
                    f"postgresql://{self.database_connection.user_name}"
                    f"@{self.database_connection.host}"
                    f":{self.database_connection.port}"
                    f"/{self.database_connection.database_name}"
                )
            return out_connection_string

        return None

    @property
    def slug(self) -> str:
        """Concatenate some attributes to build a slug.

        Returns:
            slugified metadataset name and other attributes
        """
        to_slug = ""

        if isinstance(self, MetaDatabaseTable):
            if self.database_connection.database_name:
                to_slug += f" {self.database_connection.database_name} "
            elif self.database_connection.service_name:
                to_slug += f" {self.database_connection.service_name} "
            to_slug += f" {self.schema_name} "
        elif isinstance(self, (MetaVectorDataset, MetaRasterDataset)):
            to_slug += f" {self.parent_folder_name} "

        to_slug += f" {self.name}"

        return sluggy(to_slug)

    def signature(
        self,
        hashable_attributes: tuple = (
            "bands_count",
            "crs_name",
            "crs_type",
            "dataset_type",
            "envelope",
            "features_objects_count",
            "feature_attributes",
            "format_gdal_long_name",
            "geometry_type",
            "name",
            "path_as_str",
            "schema_name",
            "storage_type",
        ),
    ) -> str:
        """Calculate a hash cumulating certain attributes values.

        hashable_attributes: object attributes to include in hash.
        """
        # instanciate the hash
        hasher = sha256(usedforsecurity=False)

        # parse attributes
        for obj_attribute in hashable_attributes:
            # because hash.update requires a
            if attr_value := getattr(self, obj_attribute, None):
                try:
                    if isinstance(attr_value, str):
                        hasher.update(attr_value.encode("UTF-8"))
                    elif isinstance(attr_value, (float, int)):
                        hasher.update(str(attr_value).encode("UTF-8"))
                    elif isinstance(attr_value, dict):
                        hasher.update(hash(frozenset(attr_value.items())))
                    elif (
                        isinstance(attr_value, tuple)
                        and obj_attribute == "feature_attributes"
                    ):
                        for feature_attribute in attr_value:
                            hasher.update(feature_attribute.signature.encode("UTF-8"))
                    else:
                        hasher.update(hash(str(attr_value).encode("UTF-8")))
                except TypeError as err:
                    logger.info(
                        f"Impossible to hash {obj_attribute} value "
                        f"({attr_value, type(attr_value)}). Trace: {err}",
                    )

        return hasher.hexdigest()


@dataclass
class MetaVectorDataset(MetaDataset):
    """Vector dataset abstraction model."""

    feature_attributes: list[AttributeField] | None = None
    features_objects_count: int = 0
    geometry_type: str | None = None

    @property
    def count_feature_attributes(self) -> int | None:
        """Return the length of 'feature_attributes' attribute.

        Returns:
            int | None: number of attribute fields related to the layer or None if no
            feature atttributes listed
        """
        if self.feature_attributes is not None:
            return len(self.feature_attributes)

        return None

    @property
    def as_markdown_feature_attributes(self) -> str:
        """Return feature attributes as a Markdown table.

        Returns:
            string containing markdown table
        """
        if self.feature_attributes is None:
            return ""

        out_markdown = "\n| name | type | length | precision |\n"
        out_markdown += "| :--- | :--: | :----: | :-------: |\n"
        for feature_attribute in self.feature_attributes:
            out_markdown += (
                f"| {feature_attribute.name} | "
                f"{feature_attribute.data_type} | "
                f"{feature_attribute.length} | "
                f"{feature_attribute.precision} |\n"
            )

        return out_markdown


@dataclass
class MetaDatabaseFlat(MetaDataset):
    """Database table abstraction model."""

    layers: list[MetaVectorDataset] | None = None

    @property
    def cumulated_count_feature_attributes(self) -> int | None:
        """Calculate the total number of attribute fields of every layer.

        Returns:
            int | None: total number of attribute fields or None if no layers listed
        """
        if self.layers is not None:
            return sum([layer.count_feature_attributes for layer in self.layers])

        return None

    @property
    def cumulated_count_feature_objects(self) -> int | None:
        """Calculate the total number of feature objects of every layer.

        Returns:
            int | None: total number of feature objects or None if no layers listed
        """
        if self.layers is not None:
            return sum([layer.features_objects_count for layer in self.layers])

        return None

    @property
    def count_layers(self) -> int | None:
        """Calculate the total number of layers.

        Returns:
            int | None: total number of layers or None if no layers listed
        """
        if self.layers is not None:
            return len(self.layers)

        return None


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

    @property
    def as_markdown_image_metadata(self) -> str:
        """Return raster metadata as a Markdown table.

        Returns:
            string containing markdown table
        """
        out_markdown = "\n| Key | value |\n"
        out_markdown += "| :---- | :-: |\n"
        out_markdown += f"| Bands count | {self.bands_count}\n"
        out_markdown += f"| Columns count | {self.columns_count}\n"
        out_markdown += f"| Rows count | {self.rows_count}\n"
        out_markdown += f"| Compression rate | {self.compression_rate}\n"

        return out_markdown


# ############################################################################
# #### Stand alone program ########
# #################################
if __name__ == "__main__":
    """standalone execution"""
