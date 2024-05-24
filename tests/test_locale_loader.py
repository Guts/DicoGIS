#! python3

"""
    Usage from the repo root folder:
        python -m unittest tests.test_locale_loader
"""

# #############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import locale
import unittest
from pathlib import Path

# package
from dicogis.utils.texts import TextsManager

# #############################################################################
# ########## Classes ###############
# ##################################


class TestLocaleLoader(unittest.TestCase):
    """Test class."""

    #  -- Tests ------------------------------------------------------------
    def test_translated_text_english(self):
        txtmngr = TextsManager(locale_folder=Path("locale"))
        self.assertIsNone(txtmngr.language_code)

        # English
        en_txts = txtmngr.load_texts(dico_texts={}, language_code="EN")
        self.assertIsInstance(en_txts, dict)
        self.assertIsInstance(txtmngr.language_code, str)
        self.assertEqual(txtmngr.language_code, "EN")

    def test_translated_text_french(self):
        txtmngr = TextsManager(locale_folder=Path("locale"))
        self.assertIsNone(txtmngr.language_code)
        # French
        fr_txts = txtmngr.load_texts(dico_texts={}, language_code="FR")
        self.assertIsInstance(fr_txts, dict)
        self.assertIsInstance(txtmngr.language_code, str)
        self.assertEqual(txtmngr.language_code, "FR")

    def test_translated_text_spanish(self):
        txtmngr = TextsManager(locale_folder=Path("locale"))
        self.assertIsNone(txtmngr.language_code)
        # Spanish
        sp_txts = txtmngr.load_texts(dico_texts={}, language_code="ES")
        self.assertIsInstance(sp_txts, dict)
        self.assertIsInstance(txtmngr.language_code, str)
        self.assertEqual(txtmngr.language_code, "ES")

    def test_translated_text_fallback(self):
        txtmngr = TextsManager(locale_folder=Path("locale"))
        self.assertIsNone(txtmngr.language_code)
        # Spanish
        translated_txts = txtmngr.load_texts()
        self.assertIsInstance(translated_txts, dict)
        self.assertIsInstance(txtmngr.language_code, str)
        self.assertEqual(txtmngr.language_code, "EN")

    def test_translated_text_tuple(self):
        txtmngr = TextsManager(locale_folder=Path("locale"))
        self.assertIsNone(txtmngr.language_code)
        # default
        default_txts = txtmngr.load_texts(
            dico_texts={}, language_code=locale.getlocale()
        )
        self.assertIsInstance(default_txts, dict)

    def test_translated_text_isolentgh(self):
        txtmngr = TextsManager(locale_folder=Path("locale"))
        self.assertIsNone(txtmngr.language_code)

        en_txts = txtmngr.load_texts(dico_texts={}, language_code="EN")
        sp_txts = txtmngr.load_texts(dico_texts={}, language_code="ES")
        fr_txts = txtmngr.load_texts(dico_texts={}, language_code="FR")

        # checks
        self.assertTrue(len(en_txts) == len(fr_txts) == len(sp_txts))


# #############################################################################
# ##### Main #######################
# ##################################
if __name__ == "__main__":
    unittest.main()
