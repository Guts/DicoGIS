#! python3  # noqa: E265


# ##############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import logging
from collections import OrderedDict

# 3rd party libraries
try:
    from osgeo import ogr, osr
except ImportError:
    import ogr, osr

# ############################################################################
# ######### Globals ############
# ##############################

logger = logging.getLogger(__name__)

# ##############################################################################
# ########## Classes ###############
# ##################################


class GeoInfosGenericReader(object):
    """TO DOC."""

    def __init__(self):
        """Instanciate class."""
        super(GeoInfosGenericReader, self).__init__()

    def get_extent_as_tuple(self, layer_obj):
        """Get spatial extent (bounding box)."""
        if hasattr(layer_obj, "GetExtent"):
            return (
                round(layer_obj.GetExtent()[0], 2),
                round(layer_obj.GetExtent()[1], 2),
                round(layer_obj.GetExtent()[2], 2),
                round(layer_obj.GetExtent()[3], 2),
            )
        else:
            return (None, None, None, None)

    def get_fields_details(self, layer_def) -> dict:
        """Get fields definition."""
        dico_fields = OrderedDict()
        for i in range(layer_def.GetFieldCount()):
            field = layer_def.GetFieldDefn(i)  # fields ordered
            dico_fields[field.GetName()] = (
                field.GetTypeName(),
                field.GetWidth(),
                field.GetPrecision(),
            )
        # end of function
        return dico_fields

    def get_geometry_type(self, layer: ogr.Layer) -> str:
        """Get geometry type human readable."""
        try:
            logger.debug(ogr.GeometryTypeToName(layer.GetGeomType()))
            # if layer.GetGeomType():
            #     geom_type = layer.GetGeomType()
            #     layer.ResetReading()
            #     logger.error(geom_type)

            #     return geom_type

            feat = layer.GetNextFeature()
            if not hasattr(feat, "GetGeometryRef"):
                logger.error("Unable to determine GeoMetryRef")
                return None
            layer_geom = feat.GetGeometryRef()
            if hasattr(layer_geom, "GetGeometryName"):
                return layer_geom.GetGeometryName()

        except Exception as err:
            logger.error(
                "Unable to retrieve geometry type for layer: {}. Trace: {}".format(
                    layer.GetName(), err
                )
            )
            return None

        # try:
        #     print("\n\nTRY")
        #     first_obj = layer.GetNextFeature()
        #     layer_geom = first_obj.GetGeometryRef()
        #     print("GOT IT")
        # except AttributeError as e:
        #     logger.error("{}: {}".format(layer.GetName(), e))
        #     first_obj = layer.GetNextFeature()
        #     if hasattr(first_obj, "GetGeometryRef"):
        #         layer_geom = first_obj.GetGeometryRef()
        #     else:
        #         logger.error("LAYER: {} has not Attribute GetGeometryRef".format(layer.GetName()))
        #         return None

    def get_srs_details(self, layer, txt):
        """get the informations about geography and geometry"""
        # SRS
        srs = layer.GetSpatialRef()
        if not srs:
            return (
                txt.get("srs_undefined", ""),
                txt.get("srs_no_epsg", ""),
                txt.get("srs_nr", ""),
            )
        else:
            pass
        srs.AutoIdentifyEPSG()
        prj = osr.SpatialReference(str(srs))
        srs_epsg = prj.GetAuthorityCode(None)

        # srs type
        srsmetod = [
            (srs.IsCompound(), txt.get("srs_comp")),
            (srs.IsGeocentric(), txt.get("srs_geoc")),
            (srs.IsGeographic(), txt.get("srs_geog")),
            (srs.IsLocal(), txt.get("srs_loca")),
            (srs.IsProjected(), txt.get("srs_proj")),
            (srs.IsVertical(), txt.get("srs_vert")),
        ]
        # searching for a match with one of srs types
        for srsmet in srsmetod:
            if srsmet[0] == 1:
                typsrs = srsmet[1]
            else:
                continue
        # in case of not match
        try:
            srs_type = typsrs
        except UnboundLocalError:
            typsrs = txt.get("srs_nr")
            srs_type = typsrs

        # handling exceptions in srs names'encoding
        try:
            if srs.GetName() is not None:
                srs_name = srs.GetName()
            elif srs.IsGeographic() and srs.GetAttrValue(str("GEOGCS")):
                srs_name = srs.GetAttrValue(str("GEOGCS")).replace("_", " ")
            elif srs.IsProjected() and srs.GetAttrValue(str("PROJCS")):
                srs_name = srs.GetAttrValue(str("PROJCS")).replace("_", " ")
            else:
                srs_name = srs.GetAttrValue(str("PROJECTION")).replace("_", " ")
        except UnicodeDecodeError:
            if srs.GetAttrValue(str("PROJCS")) != "unnamed":
                srs_name = (
                    srs.GetAttrValue(str("PROJCS")).decode("latin1").replace("_", " ")
                )
            else:
                srs_name = (
                    srs.GetAttrValue(str("PROJECTION"))
                    .decode("latin1")
                    .replace("_", " ")
                )
        finally:
            srs_epsg = srs.GetAttrValue(str("AUTHORITY"), 1)

        # World SRS default
        if srs_epsg == "4326" and srs_name == "None":
            srs_name = "WGS 84"
        else:
            pass

        return (srs_name, srs_epsg, srs_type)

    def get_title(self, layer) -> str:
        """Get layer title preventing encoding errors."""
        try:
            layer_title = layer.GetName()
        except UnicodeDecodeError:
            layer_title = layer.GetName().decode("latin1", errors="replace")
        return layer_title
