#! python3  # noqa: E265


# ##############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import logging
from pathlib import Path

# ############################################################################
# ######### Globals ############
# ##############################

logger = logging.getLogger(__name__)

# ##############################################################################
# ########## Classes ###############
# ##################################


class MetadatasetSerializerBase:
    """Base class for metadataset serializers."""

    def __init__(
        self,
        translated_texts: dict,
        output_path: Path | None = None,
        opt_raw_path: bool = False,
        opt_size_prettify: bool = True,
    ) -> None:
        """Initialize object."""
        self.translated_texts = translated_texts

        # output path
        self.output_path = output_path

        # options
        self.opt_raw_path = opt_raw_path
        self.opt_size_prettify = opt_size_prettify

    def pre_serializing(self, **kwargs):
        """Operations to run before serialization."""
        pass

    def post_serializing(self, **kwargs):
        """Operations to run after serialization."""
        pass
