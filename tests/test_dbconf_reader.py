#! python3

"""
Usage from the repo root folder:
    python -m unittest tests.test_infos_shp
"""

# #############################################################################
# ########## Libraries #############
# ##################################


# Standard library
import unittest
from pathlib import Path

# package
from dicogis.utils.db_conf_reader import read_db_conf

# #############################################################################
# ######## Globals #################
# ##################################

# variables
fixtures_folder = "tests/fixtures/"

# #############################################################################
# ########## Classes ###############
# ##################################


class TestDatabaseConfigurationReader(unittest.TestCase):
    """Test info extractor for Shapefiles."""

    # standard methods
    def setUp(self):
        """Executed before each test."""
        pass

    def tearDown(self):
        """Executed after each test."""
        pass

    #  -- Tests ------------------------------------------------------------
    def test_db_conf_reader(self):
        fixtures = Path(fixtures_folder).glob("**/*.dbconf")

        for f in fixtures:
            # run
            configured_databases = read_db_conf(f)
            self.assertIsInstance(configured_databases, list)


# #############################################################################
# ##### Main #######################
# ##################################
if __name__ == "__main__":
    unittest.main()
