#! python3  # noqa: E265

"""JSON serializer."""

# ##############################################################################
# ########## Libraries #############
# ##################################


# Standard library
import logging
from dataclasses import asdict

# project
from dicogis.export.base_serializer import MetadatasetSerializerBase
from dicogis.models.metadataset import MetaDataset

# 3rd party library


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

    def __init__(self, translated_texts: dict, opt_size_prettify: bool = True) -> None:
        """Store metadata into JSON files."""
        super().__init__(
            translated_texts=translated_texts, opt_size_prettify=opt_size_prettify
        )

    def serialize_metadaset(self, metadataset: MetaDataset) -> dict:
        return asdict(metadataset)
