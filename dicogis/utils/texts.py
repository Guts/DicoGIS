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
from pathlib import Path
from xml.etree import ElementTree as ET

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

    def __init__(self, locale_folder: Path = Path("../locale")):
        """Manage texts from a file into a dictionary used to custom program display."""
        if not locale_folder.is_dir() or not locale_folder.exists():
            raise NotADirectoryError(
                _("Locale folder must be an existing folder. Not: {}").format(
                    locale_folder.resolve()
                )
            )

        # set params as attributes
        self.locale_folder = locale_folder

    def load_texts(self, dico_texts: dict, language_code: str = "EN") -> dict:
        """Load texts according to the specified language code.

        Args:
            dico_texts (dict): dictonary to fill with localized strings
            language_code (str, optional): 2 letters prefix to pick the correct
                language. Defaults to "EN".

        Raises:
            FileNotFoundError: if language file doesn't exists

        Returns:
            dict: dictonary filled by methods
        """

        # clearing the text dictionary
        dico_texts.clear()

        # handle en_EN form
        if "_" in language_code:
            language_code = language_code.split("_")[0]

        # check file, if not exists log the error and return the default language
        lang_file = self.locale_folder / f"lang_{language_code}.xml"
        if not lang_file.is_file():
            logger.error(
                FileNotFoundError(
                    _("Langue file not found: {}").format(lang_file.resolve())
                )
            )
            return self.load_texts(dico_texts=dico_texts)

        # open xml cursor
        xml = ET.parse(lang_file)

        # Looping and gathering texts from the xml file
        for elem in xml.getroot().iter():
            dico_texts[elem.tag] = elem.text

        # end of fonction
        return dico_texts
