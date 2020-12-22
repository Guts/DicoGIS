#! python3

"""
    Usage from the repo root folder:
        python -m unittest tests.test_infos_shp
"""

# #############################################################################
# ########## Libraries #############
# ##################################

# Standard library
from pathlib import Path
import unittest

# package
from dicogis.georeaders import ReadVectorFlatDataset


# #############################################################################
# ######## Globals #################
# ##################################

# variables
fixtures_folder = "tests/fixtures/gisdata/data/good/vector/"
extension_pattern = "**/*.shp"

# #############################################################################
# ########## Classes ###############
# ##################################


class TestInfosEsriShapefiles(unittest.TestCase):
    """Test info extractor for Shapefiles."""

    # standard methods
    def setUp(self):
        """Executed before each test."""
        pass

    def tearDown(self):
        """Executed after each test."""
        pass

    #  -- Tests ------------------------------------------------------------
    def test_read(self):
        fixtures_shp = Path(fixtures_folder).glob(extension_pattern)
        georeader_vector = ReadVectorFlatDataset()
        for f in fixtures_shp:
            dico_layer = {}
            dico_txt = {}
            print(str(f.resolve()))
            georeader_vector.infos_dataset(str(f.resolve()), dico_layer, dico_txt)


# #############################################################################
# ##### Main #######################
# ##################################
if __name__ == "__main__":
    unittest.main()
