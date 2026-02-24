#! python3  # noqa: E265


"""
Name:         Texts Manager
Purpose:      Load texts from localized files to display in a parent program

Author:       Julien Moura (@geojulien)
"""

# #############################################################################
# ######### Libraries #############
# #################################

# Standard library
import gettext
import logging
from functools import lru_cache
from pathlib import Path
from xml.etree import ElementTree as ET

# package
from dicogis.constants import AvailableLocales
from dicogis.utils.utils import Utilities

# #############################################################################
# ########## Globals ###############
# ##################################

_ = gettext.gettext
logger = logging.getLogger(__name__)

# #############################################################################
# ########### Classes #############
# #################################


class TextsManager:
    """Load texts from localized files to display in a parent program"""

    def __init__(self, locale_folder: Path | None = None):
        """Manage texts from a file into a dictionary used to custom program display."""
        self.dicogis_utils = Utilities()

        if locale_folder is None:
            locale_folder = Path("locale")

        locale_folder = self.dicogis_utils.resolve_internal_path(
            internal_path=locale_folder
        )

        if not locale_folder.is_dir() or not locale_folder.exists():
            raise NotADirectoryError(
                _("Locale folder must be an existing folder. Not: {}").format(
                    locale_folder.resolve()
                )
            )

        # set params as attributes
        self.locale_folder = locale_folder
        self.language_code: str | None = None

    @lru_cache
    def load_texts(self, language_code: str | tuple = "EN") -> dict[str, str]:
        """Load texts according to the specified language code.

        Args:
            language_code (str, optional): 2 letters prefix to pick the correct
                language. Defaults to "EN".

        Raises:
            FileNotFoundError: if language file doesn't exists

        Returns:
            dict: dictonary filled by methods
        """
        translated_texts: dict[str] = {}

        # handle locale.getlocale()
        if isinstance(language_code, tuple):
            language_code = language_code[0]

        # handle en_EN form
        if "_" in language_code:
            language_code = language_code.split("_")[1]

        # handle some aliases
        if language_code.upper() in ("GB", "US"):
            language_code = "EN"

        # if language not available, fallback to English
        if not AvailableLocales.has_value(language_code):
            logger.warning(
                f"'{language_code}' is not part of available languages. "
                "Fallbacking to English."
            )
            language_code = "EN"

        self.language_code = language_code.upper()

        # check file, if not exists log the error and return the default language
        lang_file = self.locale_folder / f"lang_{language_code.upper()}.xml"
        if not lang_file.is_file():
            logger.error(
                FileNotFoundError(
                    _("Language file not found: {}").format(lang_file.resolve())
                )
            )
            return self.load_texts(language_code="EN")

        # open xml cursor
        xml = ET.parse(lang_file)

        # Looping and gathering texts from the xml file
        for elem in xml.getroot().iter():
            translated_texts[elem.tag] = elem.text

        # end of fonction
        return translated_texts


# #############################################################################
# ##### Main #######################
# ##################################
if __name__ == "__main__":
    txtmngr = TextsManager(locale_folder=Path("locale"))
    translated_texts = txtmngr.load_texts(language_code="CH")
