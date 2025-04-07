#! python3

"""
Usage from the repo root folder:
    python -m unittest tests.test_journalizer
"""

# #############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import logging
import unittest
from pathlib import Path

# package
from dicogis.__about__ import __title_clean__ as package_name
from dicogis.utils.journalizer import LogManager
from dicogis.utils.slugger import sluggy

# #############################################################################
# ########## Classes ###############
# ##################################


class TestJournalizer(unittest.TestCase):
    """Test class."""

    # standard methods
    def setUp(self):
        """Executed before each test."""
        pass

    def tearDown(self):
        """Executed after each test."""
        pass

    #  -- Tests ------------------------------------------------------------
    def test_start_journal(self):
        logmngr = LogManager(
            console_level=logging.DEBUG,
            file_level=logging.INFO,
            label=f"Testing {package_name}",
            folder=Path("tests/fixtures/"),
        )
        # add headers
        logmngr.headers()

        # checks
        self.assertIsInstance(logmngr.initial_logger_config(), logging.Logger)
        self.assertTrue(
            Path(f"tests/fixtures/{sluggy('Testing ' + package_name)}.log.1").is_file(),
        )


# #############################################################################
# ##### Main #######################
# ##################################
if __name__ == "__main__":
    unittest.main()
