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
fixtures_folder = "tests/fixtures/gisdata/data/good/"

# #############################################################################
# ########## Classes ###############
# ##################################


class TestInfosFlatRaster(unittest.TestCase):
    """Test info extractor for flat vector datasets."""

    #  -- Tests ------------------------------------------------------------
    def test_read_tif_good(self):
        fixtures_files = list(Path(fixtures_folder).joinpath("raster").glob("**/*.tif"))
        # guards against silently testing nothing if the fixtures path is wrong
        self.assertGreater(len(fixtures_files), 0, "No .tif fixture file found")

        georeader = ReadRasters()
        for fixture_file in fixtures_files:
            metadataset = georeader.infos_dataset(fixture_file)
            self.assertIsInstance(metadataset, MetaRasterDataset)
            self.assertTrue(metadataset.processing_succeeded is not False, fixture_file)
            self.assertGreater(metadataset.columns_count, 0, fixture_file)
            self.assertGreater(metadataset.rows_count, 0, fixture_file)
            self.assertGreater(metadataset.bands_count, 0, fixture_file)
            self.assertIsInstance(metadataset.data_type, str, fixture_file)
            self.assertIsInstance(metadataset.bbox, tuple, fixture_file)
            self.assertIsInstance(metadataset.origin_x, float, fixture_file)
            self.assertIsInstance(metadataset.origin_y, float, fixture_file)

    def test_read_nonexistent_raster_is_reported_as_error(self):
        """A missing raster file is reported as a failed processing rather
        than raising."""
        fixture_file = Path(fixtures_folder, "does_not_exist.tif")

        metadataset = ReadRasters().infos_dataset(fixture_file, tipo="GeoTIFF")

        self.assertFalse(metadataset.processing_succeeded)


# #############################################################################
# ##### Main #######################
# ##################################
if __name__ == "__main__":
    unittest.main()
