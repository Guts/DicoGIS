#! python3  # noqa: E265

"""JSON serializer."""

# ##############################################################################
# ########## Libraries #############
# ##################################


# Standard library
import json
import logging
from dataclasses import asdict
from pathlib import Path

# project
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
        translated_texts: dict,
        output_path: Path | None = None,
        opt_size_prettify: bool = True,
    ) -> None:
        """Store metadata into JSON files."""
        output_path.mkdir(parents=True, exist_ok=True)

        super().__init__(
            translated_texts=translated_texts,
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
            json.dump(
                asdict(metadataset),
                out_json,
                default=self.json_encoder_for_unsupported_types,
                sort_keys=True,
            )

        logger.debug(
            f"Metadataset {metadataset.path} serialized into JSON file "
            f"{output_json_filepath}"
        )
        return output_json_filepath
