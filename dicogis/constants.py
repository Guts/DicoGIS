#! python3  # noqa: E265

"""Formats enums."""

# standard library
from enum import Enum

GDAL_POSTGIS_OPEN_OPTIONS: list[str] = []


class ExtendedEnum(Enum):
    """Custom Enum with extended methods."""

    @classmethod
    def has_key(cls, name: str) -> bool:
        """Check if a certain key is present in enum.

        Source: https://stackoverflow.com/a/62065380/2556577

        Args:
            name (str): key to check.

        Returns:
            bool: True if the key exists.
        """
        return name in cls.__members__

    @classmethod
    def has_value(cls, value: str) -> bool:
        """Check if a certain value is present in enum.

        Source: https://stackoverflow.com/a/43634746/2556577

        Args:
            value (str): value to check

        Returns:
            bool: True is the value exists.
        """
        return value in cls._value2member_map_


class AvailableLocales(str, ExtendedEnum):
    """Supported locale."""

    english = "EN"
    french = "FR"
    spanish = "ES"


class JsonFlavors(str, ExtendedEnum):
    """JSON flavors."""

    dicogis = "dicogis"
    udata = "udata"


class OutputFormats(str, ExtendedEnum):
    """Supported output formats."""

    excel = "excel"
    json = "json"
    udata = "udata"


class FormatsVector(ExtendedEnum):
    """Supported vectors formats. Key=name, value = extension."""

    dgn = ".dgn"
    esri_shapefile = ".shp"
    file_geodatabase_esri = ".gdb"
    file_geodatabase_geopackage = ".gpkg"
    file_geodatabase_spatialite = ".sqlite"
    geojson = ".geojson"
    gml = ".gml"
    gxt = ".gml"
    kml = ".kml"
    mapinfo_tab = ".tab"


class FormatsRaster(ExtendedEnum):
    """Supported raster formats. Key=name, value = extension."""

    ecw = ".ecw"
    geotiff = ".geotiff"
    jpeg = ".jpeg"


SUPPORTED_FORMATS: list[ExtendedEnum] = [*FormatsVector, *FormatsRaster]

# GDAL/OGR driver short names required to read each supported format, keyed by
# the corresponding FormatsVector/FormatsRaster member name. Some formats can be
# read by more than one driver (e.g. KML via "LIBKML" or the older "KML"
# driver): any one of them being registered is enough. Used to detect formats
# that the installed GDAL build cannot actually read (some drivers, like
# "Geoconcept" or "ECW", are optional/plugin drivers not included in every
# GDAL packaging) and disable them in the GUI/CLI accordingly.
FORMAT_TO_GDAL_DRIVERS: dict[str, tuple[str, ...]] = {
    "dgn": ("DGN", "DXF"),  # the single "cdao" flag covers DXF/DWG/DGN files
    "esri_shapefile": ("ESRI Shapefile",),
    "file_geodatabase_esri": ("OpenFileGDB", "ESRI FileGDB"),
    "file_geodatabase_geopackage": ("GPKG",),
    "file_geodatabase_spatialite": ("SQLite",),
    "geojson": ("GeoJSON",),
    "gml": ("GML",),
    "gxt": ("Geoconcept",),
    "kml": ("LIBKML", "KML"),
    "mapinfo_tab": ("MapInfo File",),
    "ecw": ("ECW",),
    "geotiff": ("GTiff",),
    "jpeg": ("JPEG",),
}

# ############################################################################
# #### Stand alone program ########
# #################################
if __name__ == "__main__":
    """standalone execution"""
    assert isinstance(SUPPORTED_FORMATS, list)
    assert all([isinstance(i, ExtendedEnum) for i in SUPPORTED_FORMATS]), type(
        SUPPORTED_FORMATS[0]
    )
    assert FormatsRaster.has_key("ecw")
    assert FormatsRaster.has_key("geotiff")
    assert FormatsRaster.has_value(".geotiff")
    assert FormatsRaster.has_key("fake_raster_format") is False

    for f in SUPPORTED_FORMATS:
        print(f.name)

    print([v.value for v in AvailableLocales])
    print("EN" in AvailableLocales)
