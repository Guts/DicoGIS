#! python3

"""
Usage from the repo root folder:
    python -m unittest tests.test_infos_vector
"""

# #############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import unittest
from datetime import datetime
from pathlib import Path

# package
from dicogis.georeaders.read_vector_flat_dataset import ReadVectorFlatDataset

# #############################################################################
# ######## Globals #################
# ##################################

# variables
fixtures_folder = "tests/fixtures/gisdata/data/good/vector/"

# #############################################################################
# ########## Classes ###############
# ##################################


class TestInfosFlatVector(unittest.TestCase):
    """Test info extractor for flat vector datasets."""

    #  -- Tests ------------------------------------------------------------
    def test_read_shapefiles(self):
        fixtures_shp = Path(fixtures_folder).glob("**/*.shp")
        georeader_vector = ReadVectorFlatDataset()
        for fixture_filepath in fixtures_shp:
            # run
            metadaset = georeader_vector.infos_dataset(
                fixture_filepath.resolve(), fallback_format="ESRI Shapefiles"
            )

            # check types
            self.assertIsInstance(
                metadaset.feature_attributes,
                (list, tuple),
                fixture_filepath,
            )
            self.assertIsInstance(
                metadaset.count_feature_attributes, int, fixture_filepath
            )
            self.assertIsInstance(metadaset.bbox, tuple, fixture_filepath)
            self.assertIsInstance(metadaset.crs_name, str, fixture_filepath)
            self.assertIsInstance(
                metadaset.crs_registry_code, (str, type(None)), fixture_filepath
            )
            self.assertIsInstance(
                metadaset.crs_type, (str, type(None)), fixture_filepath
            )
            self.assertIsInstance(
                metadaset.features_objects_count, int, fixture_filepath
            )
            self.assertIsInstance(metadaset.files_dependencies, list, fixture_filepath)
            self.assertIsInstance(
                metadaset.format_gdal_long_name, str, fixture_filepath
            )
            self.assertIsInstance(metadaset.geometry_type, str, fixture_filepath)
            self.assertIsInstance(metadaset.name, str, fixture_filepath)
            self.assertIsInstance(metadaset.parent_folder_name, str, fixture_filepath)
            self.assertIsInstance(
                metadaset.storage_date_created, datetime, fixture_filepath
            )
            self.assertIsInstance(
                metadaset.storage_date_updated, datetime, fixture_filepath
            )
            self.assertIsInstance(metadaset.storage_size, int, fixture_filepath)


# #############################################################################
# ##### Main #######################
# ##################################
if __name__ == "__main__":
    unittest.main()
