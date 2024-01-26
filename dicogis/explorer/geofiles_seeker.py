#! python3  # noqa: E265

"""
    Search for geographic files according to the required formats.
"""

# #############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import logging
from os import getlogin
from pathlib import Path

# submodules
from scan_offline import _
from scan_offline.explorer import FORMATS_MATRIX, FormatYamlReader

# #############################################################################
# ########## Globals ###############
# ##################################

logger = logging.getLogger(__name__)

# ##############################################################################
# ########## Classes ###############
# ##################################


class GeofilesExplorer:
    """Used to store Isogeo API results into an Excel worksheet (.xlsx)

    :param Path start_folder: parent folder where to start looking
    :param tuple formats: selected formats to look for. Others formats will be ignored.
    :param Path definitions_folder: folder containing formats definitons overriding embedded matrix
    """

    # attributes
    files_by_formats = {}
    formats_definitions = FORMATS_MATRIX

    def __init__(
        self,
        start_folder: Path,
        formats: tuple,
        definitions_folder: Path = None,
    ):
        """Instanciating the geofiles seeker."""
        # check parent folder
        start_folder = Path(start_folder)
        if not start_folder.is_dir():
            raise OSError(
                _(
                    "Directory {} doesn't exist or it's not reachable for the user: {}"
                ).format(start_folder, getlogin())
            )
        self.start_folder = Path(start_folder)

        # check definitions folder
        self.definitions_folder = definitions_folder
        if definitions_folder is not None:
            definitions_folder = Path(definitions_folder)
            if definitions_folder.is_dir():
                self.definitions_folder = Path(definitions_folder)
                self.formats_definitions = self.load_overriding_definitions(
                    FORMATS_MATRIX, self.definitions_folder
                )
            else:
                logger.error(
                    IOError(
                        _(
                            "Folder of formats definitions {} doesn't exist "
                            "or it's not reachable for the user: {}"
                        ).format(definitions_folder, getlogin())
                    )
                )
        else:
            logger.debug(
                "No folder with custom formats definitions, so use only embedded formats."
            )

        # check formats
        self.formats = []  # list of formats named tuples
        formats_reversed_matrix = self.reverse_matrix()
        for frmt in formats:
            if frmt in self.formats_definitions:
                # match based on format code
                self.formats.append(self.formats_definitions.get(frmt))
                logger.info(f"Format '{frmt}' found in formats codes matrix.")
            elif frmt in formats_reversed_matrix:
                self.formats.append(
                    self.formats_definitions.get(formats_reversed_matrix.get(frmt))
                )
                logger.info(
                    "Format '{}' found in formats alternative names matrix (reversed).".format(
                        frmt
                    )
                )
            else:
                logging.warning(
                    "Format '{}' is not an accepted value. It'll be ignored. "
                    "Must be one of: {}".format(
                        frmt, " | ".join(self.formats_definitions)
                    )
                )

        # list of formats codes (names). Just a shortcut for information to display (log, console...)
        self.formats_codes = sorted([i.name for i in self.formats])
        self.formats_fme_short_names = sorted([i.fme_short_name for i in self.formats])

    @classmethod
    def load_overriding_definitions(
        self, in_formats_matrix: dict, definitions_folder: Path
    ) -> dict:
        """Browse the specified folder and its children to find formats definitions and override \
            embedded matrix (class attribute).

        :param dict in_formats_matrix: formats matrix to override
        :param Path definitions_folder: Path to the folder containgin the format definitions (YAML files). \
            Defaults to: None - optional
        """
        # check folder path
        if isinstance(definitions_folder, str):
            definitions_folder = Path(definitions_folder)

        if not definitions_folder.is_dir():
            logger.error(IOError("Path is not a folder."))
            return in_formats_matrix

        # check if definitions file exist
        li_yaml_files = sorted(list(definitions_folder.glob("*.y*ml")))
        if not len(li_yaml_files):
            logger.debug(f"No YAML file found into folder: {definitions_folder}")
            return in_formats_matrix

        # parse them
        for yaml_file in li_yaml_files:
            # load format definition
            try:
                format_definition = FormatYamlReader(yaml_file).as_format_matcher
                logger.info(
                    "Overriding format definition found: {}".format(
                        format_definition.name
                    )
                )
            except Exception:
                logger.warning(
                    "Format definition is incorrect and will be ignored: {}".format(
                        yaml_file
                    )
                )
                continue

            # replace or add it
            in_formats_matrix[format_definition.isogeo_code] = format_definition

        return in_formats_matrix

    @classmethod
    def reverse_matrix(self) -> dict:
        """Parse formats matrix and return a new dictionary with alternative names as keys.

        :returns: dictionary of format alternative names
        :rtype: dict
        """
        # out dictionary
        dict_reversed_matrix = {}
        # parse matrix
        for frmt_code in self.formats_definitions:
            frmt = self.formats_definitions.get(frmt_code)
            if frmt.alternative_names:
                for alt_name in frmt.alternative_names:
                    dict_reversed_matrix[alt_name] = frmt_code

        return dict_reversed_matrix

    def seek(self):
        """Parse file system from the start_folder and applying patterns matching each formats.

        :returns: dictionary of paths to datasets
        :rtype: dict
        """
        for frmt in self.formats:
            if frmt.storage_kind == "files":
                logger.info(
                    "Looking for {} files in {}...".format(
                        frmt.extension, self.start_folder
                    )
                )
                # listing files paths
                li_frmt_paths = sorted(self.start_folder.glob(f"**/*{frmt.extension}"))
                # storing paths
                if li_frmt_paths:
                    self.files_by_formats[frmt.isogeo_code] = li_frmt_paths
                    logger.info(
                        "Found {} elements matching format {}".format(
                            len(li_frmt_paths), frmt.name
                        )
                    )
            elif frmt.storage_kind == "directory":
                logger.info(
                    "Looking for {} directories in {}...".format(
                        frmt.extension, self.start_folder
                    )
                )
                # listing files paths
                li_frmt_paths = sorted(self.start_folder.glob(f"**/*{frmt.extension}/"))
                # storing paths
                if li_frmt_paths:
                    self.files_by_formats[frmt.isogeo_code] = li_frmt_paths
                    logger.info(
                        "Found {} elements matching format {}".format(
                            len(li_frmt_paths), frmt.name
                        )
                    )
            elif frmt.storage_kind == "sgbd":
                logger.info(
                    "Looking for {} files (SGBD configuration) in {}...".format(
                        frmt.extension, self.start_folder
                    )
                )
                # listing files paths
                li_frmt_paths = sorted(self.start_folder.glob(f"**/*{frmt.extension}/"))
                # storing paths
                if li_frmt_paths:
                    self.files_by_formats[frmt.isogeo_code] = li_frmt_paths
                    logger.info(
                        "Found {} elements matching format {}".format(
                            len(li_frmt_paths), frmt.name
                        )
                    )
            else:
                pass


# #############################################################################
# ##### Main #######################
# ##################################
if __name__ == "__main__":
    geoexplorer = GeofilesExplorer(
        start_folder=r"C:\Users\JulienMOURA\ISOGEO\SIG - Documents\TESTS",
        formats=("esri_shp", "filegdb"),
    )
    # print(geoexplorer.reverse_matrix())
    # print(geoexplorer.formats[0].isogeo_code)
    # print(geoexplorer.seek())
    # print(list(geoexplorer.start_folder.glob("**/*.gdb/")))
    # for p in geoexplorer.files_by_formats.get("filegdb"):
    #     print(p.is_dir())
