#! python3  # noqa: E265

"""
Data format model.
"""

# ############################################################################
# ######### Libraries #############
# #################################

# Standard library
from __future__ import (
    annotations,  # used to manage type annotation for method that return Self in Python < 3.11
)

from dataclasses import dataclass

# ############################################################################
# ######### Classes #############
# ###############################


@dataclass
class FormatMatcher:
    """Model for a format of dataset to be scanned.

    :param str name: name of the format. Example: 'ESRI File Geodatabase'
    :param list alternative_names: potential alternative names. Example: ['esri_filegdb', 'filegdb']
    :param str storage_kind: type of storage: directory, database, files
    :param str gdal_short_name: short name of the format in the FME datum (referential). Example: 'GEODATABASE_FILE'
    :param str extension: extension for files and directorie. Example : '.gdb'
    :param str dependencies_required: list of extensions of potential required dependencies. Example: ['.dbf', '.shx'].
    :param str dependencies_optional: list of extensions of potential optional dependencies. Example: ['.prj','.sbn', '.sbx'].
    """

    name: str
    alternative_names: list[str]
    data_structure: str
    gdal_long_name: str
    gdal_short_name: str
    extension: str
    dependencies_required: list[str]
    dependencies_optional: list[str]
    storage_kind: str
