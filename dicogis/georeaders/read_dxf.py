#! python3  # noqa: E265

"""Reader for DXF files."""

# ############################################################################
# ######### Libraries #############
# #################################

# Standard library
import logging

# package
from dicogis.georeaders.read_vector_flat_dataset import ReadVectorFlatDataset


# #############################################################################
# ########## Globals ###############
# ##################################

logger = logging.getLogger(__name__)

# ############################################################################
# ######## Classes #############
# ###############################


class ReadCadDxf(ReadVectorFlatDataset):
    """Reader for geographic dataset stored as flat database files or folders."""

    def __init__(self, localized_strings: dict | None = None) -> None:
        """Class constructor.

        Args:
            localized_strings: translated strings. Defaults to the system locale's.
        """
        super().__init__(dataset_type="flat_cad", localized_strings=localized_strings)


# ###########################################################################
# #### Stand alone program ########
# #################################
if __name__ == "__main__":
    """Standalone execution."""
    pass
