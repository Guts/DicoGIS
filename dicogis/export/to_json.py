#! python3  # noqa: E265

"""JSON serializer."""

# ##############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import json
import logging
from dataclasses import asdict
from os import getenv
from pathlib import Path
from typing import Literal

# project
from dicogis.__about__ import __version__
from dicogis.constants import JsonFlavors
from dicogis.export.base_serializer import MetadatasetSerializerBase
from dicogis.models.metadataset import MetaDataset
from dicogis.utils.slugger import sluggy

# ##############################################################################
# ############ Globals ############
# #################################

# LOG
logger = logging.getLogger(__name__)


# ##############################################################################
# ########## Classes ###############
# ##################################


class MetadatasetSerializerJson(MetadatasetSerializerBase):
    """Export to JSON."""

    def __init__(
        self,
        # custom
        flavor: Literal[JsonFlavors.dicogis, JsonFlavors.udata] = "dicogis",
        # inherited
        localized_strings: dict | None = None,
        output_path: Path | None = None,
        opt_size_prettify: bool = True,
    ) -> None:
        """Store metadata into JSON files."""
        output_path.mkdir(parents=True, exist_ok=True)
        self.flavor = flavor

        super().__init__(
            localized_strings=localized_strings,
            opt_size_prettify=opt_size_prettify,
            output_path=output_path,
        )

    def json_encoder_for_unsupported_types(self, obj_to_encode: object) -> str:
        """Encode objects which are not serializable as they are by json.dump.
        Typically: pathlib.Path.

        Args:
            obj_to_encode: object to encode in JSON

        Returns:
            encoded object as string
        """
        if isinstance(obj_to_encode, Path):
            return str(obj_to_encode)

    def as_udata(self, metadataset: MetaDataset) -> dict:
        """Serialize metadaset in a data structure matching udata dataset schema.

        Args:
            metadataset: input metadataset to serialize

        Returns:
            serialized as dict
        """
        out_dict = {
            "title": metadataset.name,
            "slug": sluggy(text_to_slugify=metadataset.slug),
            "description": metadataset.as_markdown_description,
            "extras": {
                "dicogis_original_path": metadataset.path_as_str,
                "dicogis_signature": metadataset.signature(),
                "dicogis_version": __version__,
            },
            "tags": [
                metadataset.format_gdal_long_name,
                metadataset.format_gdal_short_name,
                metadataset.crs_name if metadataset.crs_name else "srs_undefined",
            ],
        }

        # add udata organization if set as environment variable
        if udata_organization_id := getenv("DICOGIS_UDATA_ORGANIZATION_ID"):
            out_dict["organization"] = f"{udata_organization_id}"

        return out_dict

    def serialize_metadaset(self, metadataset: MetaDataset) -> Path:
        """Serialize input metadataset as JSON file stored in output_path.

        Args:
            metadataset: metadataset to serialize

        Returns:
            path to the generated JSON file
        """
        output_json_filepath = self.output_path.joinpath(
            f"{sluggy(metadataset.name)}.json"
        )

        with output_json_filepath.open(mode="w", encoding="UTF-8") as out_json:
            if self.flavor == "dicogis":
                json.dump(
                    asdict(metadataset),
                    out_json,
                    default=self.json_encoder_for_unsupported_types,
                    sort_keys=True,
                )
            elif self.flavor == "udata":
                json.dump(
                    self.as_udata(metadataset),
                    out_json,
                    default=self.json_encoder_for_unsupported_types,
                    sort_keys=True,
                )

        logger.debug(
            f"Metadataset {metadataset.path} serialized into JSON file "
            f"{output_json_filepath}"
        )
        return output_json_filepath
