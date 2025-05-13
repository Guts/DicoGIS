#! python3

"""
Usage from the repo root folder:
    python -m unittest tests.test_georeader_raster
"""

# #############################################################################
# ########## Libraries #############
# ##################################

import unittest

# Standard library
from pathlib import Path

# package
from dicogis.georeaders.read_raster import ReadRasters
from dicogis.models.metadataset import MetaRasterDataset

# #############################################################################
# ######## Globals #################
# ##################################

# variables
fixtures_folder = "tests/fixtures/gisdata/"

# #############################################################################
# ########## Classes ###############
# ##################################


class TestInfosFlatRaster(unittest.TestCase):
    """Test info extractor for flat vector datasets."""

    #  -- Tests ------------------------------------------------------------
    def test_read_tif_good(self):
        fixtures_files = Path(fixtures_folder).joinpath("raster").glob("**/*.tif")
        georeader = ReadRasters()
        for fixture_file in fixtures_files:
            metadataset = georeader.infos_dataset(fixture_file)
            self.assertIsInstance(metadataset, MetaRasterDataset)


# #############################################################################
# ##### Main #######################
# ##################################
if __name__ == "__main__":
    unittest.main()
