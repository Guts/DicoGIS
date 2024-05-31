#! python3  # noqa: E265


# ##############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import logging
from pathlib import Path

# project
from dicogis.utils.texts import TextsManager

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
        localized_strings: dict | None = None,
        output_path: Path | None = None,
        opt_raw_path: bool = False,
        opt_size_prettify: bool = True,
    ) -> None:
        """Initialize object."""
        self.localized_strings = localized_strings
        if self.localized_strings is None:
            self.localized_strings = TextsManager().load_texts()

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
