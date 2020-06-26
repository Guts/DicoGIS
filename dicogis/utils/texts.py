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
from xml.etree import ElementTree as ET  # XML parsing and writer

# #############################################################################
# ########## Globals ###############
# ##################################

_ = gettext.gettext
logger = logging.getLogger(__name__)

# #############################################################################
# ########### Classes #############
# #################################


class TextsManager:
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

    def load_texts(self, dico_texts: dict, lang: str = "EN") -> dict:
        """Load texts according to the selected language.

        :param dict dico_texts: ordered dictonary filled by methods
        :param str lang: 2 letters prefix to pick the correct language. Defaults to: "EN" - optional

        :raises FileNotFoundError: if language file doesn't exists

        :return: [description]
        :rtype: dict
        """
        # clearing the text dictionary
        dico_texts.clear()

        # check file
        lang_file = self.locale_folder / "lang_{}.xml".format(lang)
        if not lang_file.is_file():
            raise FileNotFoundError(
                _("Langue file not found: {}").format(lang_file.resolve())
            )

        # open xml cursor
        xml = ET.parse(lang_file)

        # Looping and gathering texts from the xml file
        for elem in xml.getroot().getiterator():
            dico_texts[elem.tag] = elem.text

        # end of fonction
        return dico_texts


# #############################################################################
# #### Stand alone program ########
# #################################

if __name__ == "__main__":
    """ standalone execution """
    pass
