#! python3  # noqa: E265

"""Models defining a dataset or database formats."""

# #############################################################################
# ########## Libraries #############
# ##################################

from dataclasses import dataclass

# ##############################################################################
# ########## Classes ###############
# ##################################


@dataclass
class DatabaseConfig:
    """Model for configuration settings of a database stored into a SGBD."""

    name: str
    host: str
    port: int
    username: str
    password: str
    schemas: list[str]
    esri_sde: bool = False


@dataclass
class FormatMatcher:
    """Model for a dataset format.

    :param str name: name of the format. Example: 'ESRI File Geodatabase'
    :param list alternative_names: potential alternative names. Example: \
            ['esri_filegdb', 'filegdb']
    :param str storage_kind: type of storage: directory, database, files
    :param str extension: extension for files and directorie. Example : '.gdb'
    :param str dependencies_required: list of extensions of potential required \
        dependencies. Example: ['.dbf', '.shx'].
    :param str dependencies_optional: list of extensions of potential optional \
        dependencies. Example: ['.prj','.sbn', '.sbx'].
    """

    alternative_names: list
    data_structure: str
    dependencies_optional: list
    dependencies_required: list
    extension: str
    name: str
    storage_kind: str
