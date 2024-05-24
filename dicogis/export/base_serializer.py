#! python3  # noqa: E265


# ##############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import logging

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
        opt_raw_path: bool = False,
        opt_size_prettify: bool = True,
    ) -> None:
        """Store metadata into JSON files."""
        self.translated_texts = translated_texts

        # options
        self.opt_raw_path = opt_raw_path
        self.opt_size_prettify = opt_size_prettify

    def pre_serializing(
        self,
        has_vector: bool = False,
        has_raster: bool = False,
        has_filedb: bool = False,
        has_mapdocs: bool = False,
        has_cad: bool = False,
        has_sgbd: bool = False,
    ):
        """Set workbook's sheets accordingly to metadata types.

        Args:
            has_vector (bool, optional): _description_. Defaults to False.
            has_raster (bool, optional): _description_. Defaults to False.
            has_filedb (bool, optional): _description_. Defaults to False.
            has_mapdocs (bool, optional): _description_. Defaults to False.
            has_cad (bool, optional): _description_. Defaults to False.
            has_sgbd (bool, optional): _description_. Defaults to False.
        """
        pass
