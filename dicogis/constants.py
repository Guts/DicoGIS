from enum import Enum


class FormatsVector(str, Enum):
    """Supported vectors formats.

    Args:
        str (_type_): _description_
        Enum (_type_): _description_
    """

    esri_shapefile = "shp"
    geojson = "GeoJSON"
    gml = "GML"
    kml = "KML"
    mapinfo_tab = "tab"


class FormatsRaster(str, Enum):
    """Suported raster formats.

    Args:
        str (_type_): _description_
        Enum (_type_): _description_
    """

    geotiff = "geotiff"
    jpeg = "jpeg"


SUPPORTED_FORMATS = [*FormatsVector, *FormatsRaster]
