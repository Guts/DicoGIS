#! python3  # noqa: E265


"""
# Name:         InfosSHP
# Purpose:      Use GDAL/OGR library to extract informations about
#                   geographic data. It permits a more friendly use as
#                   submodule.
#
# Author:       Julien Moura (https://github.com/Guts/)
"""


# ############################################################################
# ######### Libraries #############
# #################################
# Standard library
import logging
from os import chdir, path
from time import localtime, strftime

# 3rd party libraries
try:
    from osgeo import gdal
    from osgeo import ogr  # handler for vector spatial files
except ImportError:
    import gdal
    import ogr  # handler for vector spatial files

# submodules
try:
    from .gdal_exceptions_handler import GdalErrorHandler
    from .geo_infos_generic import GeoInfosGenericReader
    from .geoutils import Utils
except ValueError:
    from gdal_exceptions_handler import GdalErrorHandler
    from geo_infos_generic import GeoInfosGenericReader
    from geoutils import Utils

# ############################################################################
# ######### Globals ############
# ##############################

gdal_err = GdalErrorHandler()
georeader = GeoInfosGenericReader()
youtils = Utils()

# ############################################################################
# ######### Classes #############
# ###############################


class ReadGXT:
    def __init__(self, layerpath, dico_layer, tipo, txt=""):
        """Uses OGR functions to extract basic informations about
        geographic vector file (handles shapefile or MapInfo tables)
        and store into dictionaries.

        layerpath = path to the geographic file
        dico_layer = dictionary for global informations
        dico_fields = dictionary for the fields' informations
        li_fieds = ordered list of fields
        tipo = format
        text = dictionary of text in the selected language

        """
        # handling ogr specific exceptions
        errhandler = gdal_err.handler
        gdal.PushErrorHandler(errhandler)
        # gdal.UseExceptions()
        ogr.UseExceptions()
        self.alert = 0

        # changing working directory to layer folder
        chdir(path.dirname(layerpath))

        # raising corrupt files
        try:
            source = ogr.Open(layerpath)  # OGR driver
        except Exception as e:
            logging.error(e)
            self.alert = self.alert + 1
            youtils.erratum(dico_layer, layerpath, "err_corrupt")
            dico_layer["err_gdal"] = gdal_err.err_type, gdal_err.err_msg
            return None

        # raising incompatible files
        if not source:
            """if file is not compatible"""
            self.alert += 1
            dico_layer["err_gdal"] = gdal_err.err_type, gdal_err.err_msg
            youtils.erratum(dico_layer, layerpath, "err_nobjet")
            return None
        else:
            layer = source.GetLayer()  # get the layer
            pass

        # dataset name, title and parent folder
        try:
            dico_layer["name"] = path.basename(layerpath)
            dico_layer["folder"] = path.dirname(layerpath)
        except AttributeError as err:
            logging.error(err)
            dico_layer["name"] = path.basename(layer.GetName())
            dico_layer["folder"] = path.dirname(layer.GetName())
        dico_layer["title"] = dico_layer.get("name")[:-4].replace("_", " ").capitalize()

        # dependencies and total size
        dependencies = youtils.list_dependencies(layerpath, "auto")
        dico_layer["dependencies"] = dependencies
        dico_layer["total_size"] = youtils.sizeof(layerpath, dependencies)

        # Getting basic dates
        crea, up = path.getctime(layerpath), path.getmtime(layerpath)
        dico_layer["date_crea"] = strftime("%Y/%m/%d", localtime(crea))
        dico_layer["date_actu"] = strftime("%Y/%m/%d", localtime(up))

        # features
        layer_feat_count = layer.GetFeatureCount()
        dico_layer["num_obj"] = layer_feat_count
        if layer_feat_count == 0:
            """if layer doesn't have any object, return an error"""
            self.alert += 1
            youtils.erratum(dico_layer, layerpath, "err_nobjet")
            return None
        else:
            pass

        # fields
        layer_def = layer.GetLayerDefn()
        dico_layer["num_fields"] = layer_def.GetFieldCount()
        dico_layer["fields"] = georeader.get_fields_details(layer_def)

        # geometry type
        dico_layer["type_geom"] = georeader.get_geometry_type(layer)

        # SRS
        srs_details = georeader.get_srs_details(layer, txt)
        dico_layer["srs"] = srs_details[0]
        dico_layer["epsg"] = srs_details[1]
        dico_layer["srs_type"] = srs_details[2]

        # spatial extent
        extent = georeader.get_extent_as_tuple(layer)
        dico_layer["xmin"] = extent[0]
        dico_layer["xmax"] = extent[1]
        dico_layer["ymin"] = extent[2]
        dico_layer["ymax"] = extent[3]

        # warnings messages
        if self.alert:
            dico_layer["err_gdal"] = gdal_err.err_type, gdal_err.err_msg
        else:
            pass

        # safe exit
        del source


# ############################################################################
# #### Stand alone program ########
# #################################
if __name__ == "__main__":
    """Standalone execution."""
    pass
