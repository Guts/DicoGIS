#! python3  # noqa: E265

"""
    Matching table of formats and their extensions, types, etc.

    Resources:

        - https://app.isogeo.com/api/v1/formats
        - https://github.com/isogeo/isogeo-worker-client-fme/blob/master/lib/formats/file.js

"""

# #############################################################################
# ########## Libraries #############
# ##################################

# Standard library
from pathlib import Path
from typing import NamedTuple

# ##############################################################################
# ########## Classes ###############
# ##################################


class DatabaseConfig(NamedTuple):
    """Model for configuration settings of a database stored into a SGBD."""

    name: str
    host: str
    port: int
    username: str
    password: str
    schemas: list
    esri_sde: bool


class FormatMatcher(NamedTuple):
    """Model for a format of dataset to be scanned.

    :param str editor: name of the editor. Example: 'esri'. \
        See: https://app.isogeo.com/api/v1/formats?
    :param str name: name of the format. Example: 'ESRI File Geodatabase'
    :param list alternative_names: potential alternative names. Example: ['esri_filegdb', 'filegdb']
    :param str storage_kind: type of storage: directory, database, files
    :param str fme_short_name: short name of the format in the FME datum (referential). Example: 'GEODATABASE_FILE'
    :param str isogeo_code: format code in the Isogeo API. Example: 'filegdb'
    :param str extension: extension for files and directorie. Example : '.gdb'
    :param str dependencies_required: list of extensions of potential required dependencies. Example: ['.dbf', '.shx'].
    :param str dependencies_optional: list of extensions of potential optional dependencies. Example: ['.prj','.sbn', '.sbx'].
    :param Path list_script_params: filename of the FME Workbench to use for the LIST step.\
        It's relative to the ISOGEO_SCAN_FME_SCRIPTS environment variable.
    :param Path sign_script_name: filename of the FME Workbench to use for the SIGN step.\
        It's relative to the ISOGEO_SCAN_FME_SCRIPTS environment variable.
    :param Path lookup_script_name: filename of the FME Workbench to use for the LOOKUP step.\
        It's relative to the ISOGEO_SCAN_FME_SCRIPTS environment variable.

    """

    editor: str
    data_structure: str
    name: str
    alternative_names: list
    storage_kind: str
    fme_long_name: str
    fme_short_name: str
    isogeo_code: str
    extension: str
    dependencies_required: list
    dependencies_optional: list
    list_script_name: Path
    list_script_params: list
    sign_script_name: Path
    sign_script_params: list
    lookup_script_name: Path
    lookup_script_params: list


# ##############################################################################
# ############ Globals ############
# #################################

FORMATS_MATRIX = {
    # Esri SDE
    "arcsde": FormatMatcher(
        editor="esri",
        data_structure="both",
        name="ESRI SDE Geodatabase",
        alternative_names=["arcsde", "geodatabase_sde", "sde", "sde30"],
        storage_kind="sgbd",
        fme_long_name="GEODATABASE_SDE",
        fme_short_name="GEODATABASE_SDE",
        isogeo_code="arcsde",
        extension=".sde",
        dependencies_required=[],
        dependencies_optional=[],
        list_script_name="list-esrigdb.fmw",
        list_script_params=[
            "LOG_FILE",
            "OUTPUT_JSON",
            "SDE_FILE",
            "SOURCE",
        ],
        sign_script_name="sign-esrigdb.fmw",
        sign_script_params=[
            "FEATURE_TYPES",
            "LOG_FILE",
            "NUMBER_OF_SIGNATURES",
            "OUTPUT_JSON",
            "SDE_FILE",
            "SOURCE",
        ],
        lookup_script_name="lookup-esrigdb.fmw",
        lookup_script_params=[
            "FEATURE_TYPES",
            "LOG_FILE",
            "OUTPUT_JSON",
            "SDE_FILE",
            "SOURCE",
        ],
    ),
    # Esri FileGeoDatabase
    "filegdb": FormatMatcher(
        editor="esri",
        data_structure="both",
        name="ESRI File Geodatabase",
        alternative_names=["esri_filegdb"],
        storage_kind="directory",
        fme_long_name="GEODATABASE_FILE",
        fme_short_name="GEODATABASE_FILE",
        isogeo_code="filegdb",
        extension=".gdb",
        dependencies_required=[],
        dependencies_optional=[],
        list_script_name="list-fgdb.fmw",
        list_script_params=["LOG_FILE", "OUTPUT_JSON", "SOURCE"],
        sign_script_name="sign-fgdb.fmw",
        sign_script_params=[
            "FEATURE_TYPES",
            "LOG_FILE",
            "NUMBER_OF_SIGNATURES",
            "OUTPUT_JSON",
            "SOURCE",
        ],
        lookup_script_name="lookup-fgdb.fmw",
        lookup_script_params=["FEATURE_TYPES", "LOG_FILE", "OUTPUT_JSON", "SOURCE"],
    ),
    #  GeoTIFF
    "geotiff": FormatMatcher(
        editor="osgeo",
        data_structure="raster",
        name="geotiff",
        alternative_names=["geotiff", "tiff"],
        storage_kind="files",
        fme_long_name="geotiff",
        fme_short_name="geotiff",
        isogeo_code="geotiff",
        extension=".tif",
        dependencies_required=["tab", "tfw"],
        dependencies_optional=[".aux", ".aux.xml", ".lgo", ".txt", ".wld"],
        list_script_name=None,
        list_script_params=None,
        sign_script_name=None,
        sign_script_params=None,
        lookup_script_name="lookup-raster.fmw",
        lookup_script_params=["FORMAT", "LOG_FILE", "OUTPUT_JSON", "SOURCE"],
    ),
    # Esri Shapefiles
    "shp": FormatMatcher(
        editor="esri",
        data_structure="vector",
        name="ESRI Shapefile",
        alternative_names=["esri_shp", "esri_shape", "shapefile", "shapefiles"],
        storage_kind="files",
        fme_long_name="ESRISHAPE",
        fme_short_name="ESRISHAPE",
        isogeo_code="shp",
        extension=".shp",
        dependencies_required=[".dbf", ".shx"],
        dependencies_optional=[
            ".atx",
            ".cpg",
            ".fbn",
            ".fbx",
            ".ixs",
            ".mxs",
            ".prj",
            ".sbn",
            ".sbx",
            ".shp.xml",
        ],
        list_script_name=None,
        list_script_params=None,
        sign_script_name=None,
        sign_script_params=None,
        lookup_script_name="lookup-vector.fmw",
        lookup_script_params=["LOG_FILE", "OUTPUT_JSON", "SOURCE"],
    ),
    # PostGIS
    "postgis": FormatMatcher(
        editor="osgeo",
        data_structure="both",
        name="PostGIS",
        alternative_names=["postgis", "pgis", "postgresql_postgis"],
        storage_kind="sgbd",
        fme_long_name="POSTGIS",
        fme_short_name="POSTGIS",
        isogeo_code="postgis",
        extension=".pgconf",
        dependencies_required=[],
        dependencies_optional=[],
        list_script_name="list-postgis.fmw",
        list_script_params=["LOG_FILE", "OUTPUT_JSON", "SOURCE"],
        sign_script_name="sign-postgis.fmw",
        sign_script_params=["LOG_FILE", "OUTPUT_JSON", "SOURCE"],
        lookup_script_name="lookup-postgis.fmw",
        lookup_script_params=["LOG_FILE", "OUTPUT_JSON", "SOURCE"],
    ),
}

# #############################################################################
# ##### Stand alone program ########
# ##################################
if __name__ == "__main__":
    """Standalone execution and development tests"""
    for i in FORMATS_MATRIX:
        assert isinstance(FORMATS_MATRIX.get(i), FormatMatcher)
