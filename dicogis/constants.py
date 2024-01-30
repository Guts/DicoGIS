#! python3  # noqa: E265

"""Formats enums."""

# standard library
from enum import Enum


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


class FormatsVector(ExtendedEnum):
    """Supported vectors formats. Key=name, value = extension."""

    dgn = ".dgn"
    dwg = ".dwg"
    dxf = ".dxf"
    esri_shapefile = ".shp"
    geojson = ".geojson"
    gml = ".gml"
    kml = ".kml"
    mapinfo_tab = ".tab"
    sqlite = ".sqlite"


class FormatsRaster(ExtendedEnum):
    """Suported raster formats. Key=name, value = extension."""

    ecw = ".ecw"
    geotiff = ".geotiff"
    jpeg = ".jpeg"


SUPPORTED_FORMATS = [*FormatsVector, *FormatsRaster]

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
    assert FormatsRaster.has_value("geotiff")
    assert FormatsRaster.has_key("fake_raster_format") is False
