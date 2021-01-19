#! python3  # noqa: E265


# ----------------------------------------------------------------------------
# Name:         InfosSpatialite
# Purpose:      Use OGR to read into Spatialite databases (ie SQLite with
#               geospatial extension)
#
# Author:       Julien Moura (https://github.com/Guts/)
# ----------------------------------------------------------------------------


# ############################################################################
# ######### Libraries #############
# #################################
# Standard library
import logging
from collections import OrderedDict
from os import path
from time import localtime, strftime

# 3rd party libraries
from osgeo import gdal, ogr

# #############################################################################
# ########## Globals ###############
# ##################################

logger = logging.getLogger(__name__)

# ############################################################################
# ######## Classes #############
# ###############################


class OGRErrorHandler(object):
    def __init__(self):
        """Callable error handler.

        see: http://trac.osgeo.org/gdal/wiki/PythonGotchas#Exceptionsraisedincustomerrorhandlersdonotgetcaught
        and http://pcjericks.github.io/py-gdalogr-cookbook/gdal_general.html#install-gdal-ogr-error-handler
        """
        self.err_level = gdal.CE_None
        self.err_type = 0
        self.err_msg = ""

    def handler(self, err_level, err_type, err_msg):
        """Makes errors messages more readable."""
        # available types
        err_class = {
            gdal.CE_None: "None",
            gdal.CE_Debug: "Debug",
            gdal.CE_Warning: "Warning",
            gdal.CE_Failure: "Failure",
            gdal.CE_Fatal: "Fatal",
        }
        # getting type
        err_type = err_class.get(err_type, "None")

        # cleaning message
        err_msg = err_msg.replace("\n", " ")

        # disabling OGR exceptions raising to avoid future troubles
        ogr.DontUseExceptions()

        # propagating
        self.err_level = err_level
        self.err_type = err_type
        self.err_msg = err_msg

        # end of function
        return self.err_level, self.err_type, self.err_msg


class ReadSpaDB:
    def __init__(self, spadbpath, dico_spadb, tipo, txt=""):
        """Use OGR functions to extract basic informations about
        geographic vector file
        and store into dictionaries.

        spapath = path to the Spatialite DB
        dico_spadb = dictionary for global informations
        dico_fields = dictionary for the fields' informations
        li_fieds = ordered list of fields
        tipo = format
        text = dictionary of text in the selected language
        """
        # handling ogr specific exceptions
        ogrerr = OGRErrorHandler()
        errhandler = ogrerr.handler
        gdal.PushErrorHandler(errhandler)
        ogr.UseExceptions()
        self.alert = 0

        # counting alerts
        self.alert = 0

        # opening GDB
        try:
            spadb = ogr.Open(spadbpath, 0)
        except Exception:
            self.erratum(dico_spadb, spadbpath, "err_corrupt")
            self.alert = self.alert + 1
            return None

        # GDB name and parent folder
        dico_spadb["name"] = path.basename(spadb.GetName())
        dico_spadb["folder"] = path.dirname(spadb.GetName())
        # layers count and names
        dico_spadb["layers_count"] = spadb.GetLayerCount()
        li_layers_names = []
        li_layers_idx = []
        dico_spadb["layers_names"] = li_layers_names
        dico_spadb["layers_idx"] = li_layers_idx

        # cumulated size
        total_size = path.getsize(spadbpath)
        dico_spadb["total_size"] = self.sizeof(total_size)

        # global dates
        dico_spadb["date_actu"] = strftime(
            "%d/%m/%Y", localtime(path.getmtime(spadbpath))
        )
        dico_spadb["date_crea"] = strftime(
            "%d/%m/%Y", localtime(path.getctime(spadbpath))
        )
        # total fields count
        total_fields = 0
        dico_spadb["total_fields"] = total_fields
        # total objects count
        total_objs = 0
        dico_spadb["total_objs"] = total_objs
        # parsing layers
        for layer_idx in range(spadb.GetLayerCount()):
            # dictionary where will be stored informations
            dico_layer = OrderedDict()
            # parent GDB
            dico_layer["gdb_name"] = path.basename(spadb.GetName())
            # getting layer object
            layer = spadb.GetLayerByIndex(layer_idx)
            # layer name
            li_layers_names.append(layer.GetName())
            # layer index
            li_layers_idx.append(layer_idx)
            # getting layer globlal informations
            self.infos_basics(layer, dico_layer, txt)
            # storing layer into the GDB dictionary
            dico_spadb[
                "{0}_{1}".format(layer_idx, dico_layer.get("title"))
            ] = dico_layer
            # summing fields number
            total_fields += dico_layer.get("num_fields")
            # summing objects number
            total_objs += dico_layer.get("num_obj")
            # deleting dictionary to ensure having cleared space
            del dico_layer
        # storing fileds and objects sum
        dico_spadb["total_fields"] = total_fields
        dico_spadb["total_objs"] = total_objs

        # warnings messages
        dico_spadb["err_gdal"] = ogrerr.err_type, ogrerr.err_msg

    def infos_basics(self, layer_obj, dico_layer, txt):
        """Get the global informations about the layer."""
        # title
        try:
            dico_layer["title"] = layer_obj.GetName()
        except UnicodeDecodeError:
            layerName = layer_obj.GetName().decode("latin1", errors="replace")
            dico_layer["title"] = layerName

        # features count
        dico_layer["num_obj"] = layer_obj.GetFeatureCount()

        if layer_obj.GetFeatureCount() == 0:
            """if layer doesn't have any object, return an error"""
            dico_layer["error"] = "err_nobjet"
            self.alert = self.alert + 1
        else:
            # getting geography and geometry informations
            srs = layer_obj.GetSpatialRef()
            self.infos_geos(layer_obj, srs, dico_layer, txt)

        # getting fields informations
        dico_fields = OrderedDict()
        layer_def = layer_obj.GetLayerDefn()
        dico_layer["num_fields"] = layer_def.GetFieldCount()
        self.infos_fields(layer_def, dico_fields)
        dico_layer["fields"] = dico_fields

        # end of function
        return dico_layer

    def infos_geos(self, layer_obj, srs, dico_layer, txt):
        """Get the informations about geography and geometry."""
        # SRS
        srs.AutoIdentifyEPSG()
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
            dico_layer["srs_type"] = typsrs
        except UnboundLocalError:
            typsrs = txt.get("srs_nr")
            dico_layer["srs_type"] = typsrs

        # handling exceptions in srs names'encoding
        try:
            if srs.GetAttrValue(str("PROJCS")) != "unnamed":
                dico_layer["srs"] = srs.GetAttrValue(str("PROJCS")).replace("_", " ")
            else:
                dico_layer["srs"] = srs.GetAttrValue(str("PROJECTION")).replace(
                    "_", " "
                )
        except UnicodeDecodeError:
            if srs.GetAttrValue(str("PROJCS")) != "unnamed":
                dico_layer["srs"] = (
                    srs.GetAttrValue(str("PROJCS")).decode("latin1").replace("_", " ")
                )
            else:
                dico_layer["srs"] = (
                    srs.GetAttrValue(str("PROJECTION"))
                    .decode("latin1")
                    .replace("_", " ")
                )
        finally:
            dico_layer["epsg"] = srs.GetAttrValue(str("AUTHORITY"), 1)

        # World SRS default
        if dico_layer["epsg"] == "4326" and dico_layer["srs"] == "None":
            dico_layer["srs"] = "WGS 84"
        else:
            pass

        # first feature and geometry type
        try:
            first_obj = layer_obj.GetNextFeature()
            geom = first_obj.GetGeometryRef()
        except AttributeError as err:
            logger.error(
                "Get geomtry ref failed on layer {}. Trace: {}".format(
                    layer_obj.GetName(), err
                )
            )
            first_obj = layer_obj.GetNextFeature()
            geom = first_obj.GetGeometryRef()

        # geometry type human readable
        if geom.GetGeometryName() == "POINT":
            dico_layer["type_geom"] = txt.get("geom_point")
        elif "LINESTRING" in geom.GetGeometryName():
            dico_layer["type_geom"] = txt.get("geom_ligne")
        elif "POLYGON" in geom.GetGeometryName():
            dico_layer["type_geom"] = txt.get("geom_polyg")
        else:
            dico_layer["type_geom"] = geom.GetGeometryName()

        # spatial extent (bounding box)
        dico_layer["xmin"] = round(layer_obj.GetExtent()[0], 2)
        dico_layer["xmax"] = round(layer_obj.GetExtent()[1], 2)
        dico_layer["ymin"] = round(layer_obj.GetExtent()[2], 2)
        dico_layer["ymax"] = round(layer_obj.GetExtent()[3], 2)

        # end of function
        return dico_layer

    def infos_fields(self, layer_def, dico_fields):
        """Get the informations about fields definitions."""
        for i in range(layer_def.GetFieldCount()):
            champomy = layer_def.GetFieldDefn(i)  # fields ordered
            dico_fields[champomy.GetName()] = (
                champomy.GetTypeName(),
                champomy.GetWidth(),
                champomy.GetPrecision(),
            )
        # end of function
        return dico_fields

    def sizeof(self, os_size):
        """Return size in different units depending on size.

        see http://stackoverflow.com/a/1094933
        """
        for size_cat in ["octets", "Ko", "Mo", "Go"]:
            if os_size < 1024.0:
                return "%3.1f %s" % (os_size, size_cat)
            os_size /= 1024.0
        return "%3.1f %s" % (os_size, " To")

    def erratum(self, dico_spadb, spadbpath, mess):
        """Errors handler."""
        # local variables
        dico_spadb["name"] = path.basename(spadbpath)
        dico_spadb["folder"] = path.dirname(spadbpath)
        try:
            def_couche = self.layer.GetLayerDefn()
            dico_spadb["num_fields"] = def_couche.GetFieldCount()
        except AttributeError:
            mess = mess
        finally:
            dico_spadb["error"] = mess
            dico_spadb["layers_count"] = 0
        # End of function
        return dico_spadb


# ###########################################################################
# #### Stand alone program ########
# #################################
if __name__ == "__main__":
    """Standalone execution."""
    pass
