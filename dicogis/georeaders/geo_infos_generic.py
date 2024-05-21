#! python3  # noqa: E265


# ##############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import logging
from locale import getlocale
from typing import Optional

# 3rd party libraries
from osgeo import ogr, osr

# project
from dicogis.models.feature_attributes import AttributeField
from dicogis.utils.texts import TextsManager

# ############################################################################
# ######### Globals ############
# ##############################

logger = logging.getLogger(__name__)

# ##############################################################################
# ########## Classes ###############
# ##################################


class GeoInfosGenericReader:
    """Reader for geographic dataset stored as flat files."""

    def __init__(
        self,
        localized_strings: Optional[dict] = None,
    ) -> None:
        """Initialization.

        Args:
            localized_strings (Optional[dict]): translated strings
        """
        self.localized_strings = localized_strings
        if self.localized_strings is None:
            self.localized_strings = TextsManager().load_texts(
                dico_texts=localized_strings, language_code=getlocale()[0]
            )

    def get_extent_as_tuple(
        self, ogr_layer: ogr.Layer
    ) -> tuple[Optional[float], Optional[float], Optional[float], Optional[float]]:
        """Get spatial extent (bounding box)."""
        if hasattr(ogr_layer, "GetExtent"):
            return (
                round(ogr_layer.GetExtent()[0], 2),
                round(ogr_layer.GetExtent()[1], 2),
                round(ogr_layer.GetExtent()[2], 2),
                round(ogr_layer.GetExtent()[3], 2),
            )
        else:
            return (None, None, None, None)

    def get_fields_details(
        self, ogr_layer_definition: ogr.FeatureDefn
    ) -> tuple[AttributeField]:
        """Get feature attributes from layer definition."""
        li_feature_attributes: list[AttributeField] = []
        for i in range(ogr_layer_definition.GetFieldCount()):
            field = ogr_layer_definition.GetFieldDefn(i)  # fields ordered
            li_feature_attributes.append(
                AttributeField(
                    name=field.GetName(),
                    data_type=field.GetTypeName(),
                    length=field.GetWidth(),
                    precision=field.GetPrecision(),
                )
            )

        # end of function
        return tuple(li_feature_attributes)

    def get_geometry_type(self, layer: ogr.Layer) -> str:
        """Get geometry type in a human readable format."""
        try:
            logger.debug(ogr.GeometryTypeToName(layer.GetGeomType()))
            feat = layer.GetNextFeature()
            if not hasattr(feat, "GetGeometryRef"):
                logger.error("Unable to determine GeoMetryRef")
                return None
            layer_geom = feat.GetGeometryRef()
            if hasattr(layer_geom, "GetGeometryName"):
                return layer_geom.GetGeometryName()

        except Exception as err:
            logger.error(
                f"Unable to retrieve geometry type for layer: {layer.GetName()}. "
                f"Trace: {err}"
            )
            return None

    def get_srs_details(self, layer: ogr.Layer) -> tuple[str, str, str]:
        """get the informations about geography and geometry"""
        # SRS
        srs = layer.GetSpatialRef()
        if not srs:
            return (
                self.localized_strings.get("srs_undefined", ""),
                self.localized_strings.get("srs_no_epsg", ""),
                self.localized_strings.get("srs_nr", ""),
            )
        else:
            pass
        srs.AutoIdentifyEPSG()
        prj = osr.SpatialReference(str(srs))
        srs_epsg = prj.GetAuthorityCode(None)

        # srs type
        srsmetod = [
            (srs.IsDynamic(), self.localized_strings.get("srs_dyna", "Dynamic")),
            (srs.IsCompound(), self.localized_strings.get("srs_comp", "Compound")),
            (
                srs.IsDerivedGeographic(),
                self.localized_strings.get("srs_derg", "Derived geographic"),
            ),
            (srs.IsGeocentric(), self.localized_strings.get("srs_geoc", "Geocentric")),
            (srs.IsGeographic(), self.localized_strings.get("srs_geog", "Geographic")),
            (srs.IsLocal(), self.localized_strings.get("srs_loca", "Local")),
            (srs.IsProjected(), self.localized_strings.get("srs_proj", "Projected")),
            (srs.IsVertical(), self.localized_strings.get("srs_vert", "Vertical")),
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
            typsrs = self.localized_strings.get("srs_nr")
            srs_type = typsrs

        # handling exceptions in srs names'encoding
        try:
            if srs.GetName() is not None:
                srs_name = srs.GetName()
            elif srs.IsGeographic() and srs.GetAttrValue("GEOGCS"):
                srs_name = srs.GetAttrValue("GEOGCS").replace("_", " ")
            elif srs.IsProjected() and srs.GetAttrValue("PROJCS"):
                srs_name = srs.GetAttrValue("PROJCS").replace("_", " ")
            else:
                srs_name = srs.GetAttrValue("PROJECTION").replace("_", " ")
        except UnicodeDecodeError:
            if srs.GetAttrValue("PROJCS") != "unnamed":
                srs_name = srs.GetAttrValue("PROJCS").decode("latin1").replace("_", " ")
            else:
                srs_name = (
                    srs.GetAttrValue("PROJECTION").decode("latin1").replace("_", " ")
                )
        finally:
            srs_epsg = srs.GetAttrValue("AUTHORITY", 1)

        # World SRS default
        if srs_epsg == "4326" and srs_name == "None":
            srs_name = "WGS 84"
        else:
            pass

        return (srs_name, srs_epsg, srs_type)

    def get_title(self, layer: ogr.Layer) -> str:
        """Get layer title preventing encoding errors."""
        try:
            layer_title = layer.GetName()
        except UnicodeDecodeError:
            layer_title = layer.GetName().decode("latin1", errors="replace")
        return layer_title
