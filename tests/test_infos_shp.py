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
            # run
            dico_layer = {}
            dico_txt = {}
            georeader_vector.infos_dataset(str(f.resolve()), dico_layer, dico_txt)

            # checks output keys
            self.assertIn("date_actu", dico_layer)
            self.assertIn("date_crea", dico_layer)
            self.assertIn("dependencies", dico_layer)
            self.assertIn("epsg", dico_layer)
            self.assertIn("fields", dico_layer)
            self.assertIn("folder", dico_layer)
            self.assertIn("name", dico_layer)
            self.assertIn("num_fields", dico_layer)
            self.assertIn("num_obj", dico_layer)
            self.assertIn("srs", dico_layer)
            self.assertIn("srs_type", dico_layer)
            self.assertIn("title", dico_layer)
            self.assertIn("total_size", dico_layer)
            self.assertIn("format", dico_layer)
            self.assertIn("type_geom", dico_layer)
            self.assertIn("xmin", dico_layer)
            self.assertIn("xmax", dico_layer)
            self.assertIn("ymin", dico_layer)
            self.assertIn("ymax", dico_layer)

            # check types
            self.assertIsInstance(dico_layer.get("date_actu"), str)
            self.assertIsInstance(dico_layer.get("date_crea"), str)
            self.assertIsInstance(dico_layer.get("dependencies"), list)
            self.assertIsInstance(dico_layer.get("epsg"), (str, type(None)))
            self.assertIsInstance(dico_layer.get("fields"), dict)
            self.assertIsInstance(dico_layer.get("folder"), str)
            self.assertIsInstance(dico_layer.get("name"), str)
            self.assertIsInstance(dico_layer.get("num_fields"), int)
            self.assertIsInstance(dico_layer.get("num_obj"), int)
            self.assertIsInstance(dico_layer.get("srs"), str)
            self.assertIsInstance(dico_layer.get("srs_type"), (str, type(None)))
            self.assertIsInstance(dico_layer.get("title"), str)
            self.assertIsInstance(dico_layer.get("total_size"), str)
            self.assertIsInstance(dico_layer.get("format"), str)
            self.assertIsInstance(dico_layer.get("type_geom"), str)
            self.assertIsInstance(dico_layer.get("xmin"), float)
            self.assertIsInstance(dico_layer.get("xmax"), float)
            self.assertIsInstance(dico_layer.get("ymin"), float)
            self.assertIsInstance(dico_layer.get("ymax"), float)


# #############################################################################
# ##### Main #######################
# ##################################
if __name__ == "__main__":
    unittest.main()
