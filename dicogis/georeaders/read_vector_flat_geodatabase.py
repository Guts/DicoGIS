#! python3  # noqa: E265


"""Reader for flat geodatabases."""

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


class ReadFlatDatabase(ReadVectorFlatDataset):
    """Reader for geographic dataset stored as flat database files or folders.

    Typically ESRI FileGDB, Geopackage, Spatialite...
    """

    def __init__(self):
        """Class constructor."""
        super().__init__(dataset_type="flat_database")


# ###########################################################################
# #### Stand alone program ########
# #################################
if __name__ == "__main__":
    """Standalone execution."""
    from pprint import pprint

    # SpatiaLite
    georeader = ReadFlatDatabase()
    metadataset = georeader.infos_dataset(
        source_path="/home/jmo/Documents/GIS Database/QGIS Training Data/QGIS-Training-Data-release_3.28/exercise_data/qgis-server-tutorial-data/naturalearth.sqlite",
    )
    print(metadataset.name, metadataset.count_layers, metadataset.dataset_type)

    # Geopackage
    georeader = ReadFlatDatabase()
    metadataset = georeader.infos_dataset(
        source_path="/home/jmo/Documents/GIS Database/SIRAD/SIRAD_2012.gpkg"
    )
    print(metadataset.name, metadataset.count_layers, metadataset.dataset_type)

    # Esri FileGDB
    georeader = ReadFlatDatabase()
    metadataset = georeader.infos_dataset(
        source_path="/home/jmo/Documents/GIS Database/SIRAD/SIRAD_2012.gdb"
    )
    print(metadataset.name, metadataset.count_layers, metadataset.dataset_type)
    pprint(metadataset)
