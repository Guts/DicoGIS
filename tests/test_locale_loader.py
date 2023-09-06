#! python3

"""
    Usage from the repo root folder:
        python -m unittest tests.test_locale_loader
"""

# #############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import unittest
from pathlib import Path

# package
from dicogis.utils.texts import TextsManager

# #############################################################################
# ########## Classes ###############
# ##################################


class TestLocaleLoader(unittest.TestCase):
    """Test class."""

    # standard methods
    def setUp(self):
        """Executed before each test."""
        pass

    def tearDown(self):
        """Executed after each test."""
        pass

    #  -- Tests ------------------------------------------------------------
    def test_basic(self):
        txtmngr = TextsManager(locale_folder=Path("dicogis/locale"))

        # English
        en_txts = txtmngr.load_texts(dico_texts={}, lang="EN")
        self.assertIsInstance(en_txts, dict)

        # French
        fr_txts = txtmngr.load_texts(dico_texts={}, lang="FR")
        self.assertIsInstance(fr_txts, dict)

        # Spanish
        sp_txts = txtmngr.load_texts(dico_texts={}, lang="ES")
        self.assertIsInstance(sp_txts, dict)

        # checks
        self.assertTrue(len(en_txts) == len(fr_txts) == len(sp_txts))


# #############################################################################
# ##### Main #######################
# ##################################
if __name__ == "__main__":
    unittest.main()
