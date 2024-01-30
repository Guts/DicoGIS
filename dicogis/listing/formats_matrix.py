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

# package
from dicogis.listing.models import FormatMatcher

# ##############################################################################
# ############ Globals ############
# #################################

FORMATS_MATRIX = {
    # Esri SDE
    "arcsde": FormatMatcher(
        data_structure="both",
        name="ESRI SDE Geodatabase",
        alternative_names=["arcsde", "geodatabase_sde", "sde", "sde30"],
        storage_kind="sgbd",
        extension=".sde",
        dependencies_required=[],
        dependencies_optional=[],
    ),
    # Esri FileGeoDatabase
    "filegdb": FormatMatcher(
        data_structure="both",
        name="ESRI File Geodatabase",
        alternative_names=["esri_filegdb"],
        storage_kind="directory",
        extension=".gdb",
        dependencies_required=[],
        dependencies_optional=[],
    ),
    #  GeoTIFF
    "geotiff": FormatMatcher(
        data_structure="raster",
        name="geotiff",
        alternative_names=["geotiff", "tiff"],
        storage_kind="files",
        extension=".tif",
        dependencies_required=["tab", "tfw"],
        dependencies_optional=[".aux", ".aux.xml", ".lgo", ".txt", ".wld"],
    ),
    # Esri Shapefiles
    "shp": FormatMatcher(
        data_structure="vector",
        name="ESRI Shapefile",
        alternative_names=["esri_shp", "esri_shape", "shapefile", "shapefiles"],
        storage_kind="files",
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
    ),
    # PostGIS
    "postgis": FormatMatcher(
        data_structure="both",
        name="PostGIS",
        alternative_names=["postgis", "pgis", "postgresql_postgis"],
        storage_kind="sgbd",
        extension=".pgconf",
        dependencies_required=[],
        dependencies_optional=[],
    ),
}

# #############################################################################
# ##### Stand alone program ########
# ##################################
if __name__ == "__main__":
    """Standalone execution and development tests"""
    for i in FORMATS_MATRIX:
        assert isinstance(FORMATS_MATRIX.get(i), FormatMatcher)
