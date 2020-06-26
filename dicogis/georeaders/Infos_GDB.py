#! python3  # noqa: E265


# ----------------------------------------------------------------------------
# Name:         InfosGDB
# Purpose:      Uses OGR to read into Esri File GeoDataBase.
#
# Author:       Julien Moura (https://github.com/Guts/)
#
# Python:       2.7.x
# Created:      24/05/2014
# Updated:      11/11/2014
# Licence:      GPL 3
# ----------------------------------------------------------------------------


# 3rd party libraries
# ############################################################################
# ######### Libraries #############
# #################################
# Standard library
import logging
from collections import OrderedDict  # Python 3 backported
from os import path, walk  # files and folder managing
from time import localtime, strftime

try:
    from osgeo import gdal
    from osgeo import ogr
except ImportError:
    import gdal
    import ogr

# custom submodules
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
youtils = Utils(ds_type="flat")
logger = logging.getLogger(__name__)

# ############################################################################
# ######### Classes ############
# ##############################


class ReadGDB:
    def __init__(self):
        """Class constructor."""
        # handling ogr specific exceptions
        errhandler = gdal_err.handler
        gdal.PushErrorHandler(errhandler)
        gdal.UseExceptions()
        self.alert = 0

    def infos_dataset(self, source_path, dico_dataset, txt=dict(), tipo=None):
        """Use OGR functions to extract basic informations.

        source_path = path to the File Geodatabase Esri
        dico_dataset = dictionary for global informations
        tipo = format
        txt = dictionary of text in the selected language
        """
        dico_dataset["type"] = tipo

        # opening GDB
        try:
            driver = ogr.GetDriverByName(str("OpenFileGDB"))
            src = driver.Open(source_path, 0)
            print(driver.GetName())
            # print(type(src), dir(src.GetDriver()), len(dir(src)))
            # src = gdal.OpenEx(source_path, 0)  # GDAL driver
            # print(type(src), dir(src), len(dir(src)))
            if not tipo:
                dico_dataset["type"] = driver.GetName()
            else:
                dico_dataset["type"] = tipo
                pass
        except Exception as e:
            logger.error(e)
            youtils.erratum(dico_dataset, source_path, "err_corrupt")
            self.alert = self.alert + 1
            return None

        # GDB name and parent folder
        try:
            dico_dataset["name"] = path.basename(src.GetName())
            dico_dataset["folder"] = path.dirname(src.GetName())
        except AttributeError as err:
            logger.warning(err)
            dico_dataset["name"] = path.basename(source_path)
            dico_dataset["folder"] = path.dirname(source_path)
        # layers count and names
        dico_dataset["layers_count"] = src.GetLayerCount()
        li_layers_names = []
        li_layers_idx = []
        dico_dataset["layers_names"] = li_layers_names
        dico_dataset["layers_idx"] = li_layers_idx

        # cumulated size
        dico_dataset["total_size"] = youtils.sizeof(source_path)

        # global dates
        crea, up = path.getctime(source_path), path.getmtime(source_path)
        dico_dataset["date_crea"] = strftime("%Y/%m/%d", localtime(crea))
        dico_dataset["date_actu"] = strftime("%Y/%m/%d", localtime(up))
        # total fields count
        total_fields = 0
        dico_dataset["total_fields"] = total_fields
        # total objects count
        total_objs = 0
        dico_dataset["total_objs"] = total_objs
        # parsing layers
        for layer_idx in range(src.GetLayerCount()):
            # dictionary where will be stored informations
            dico_layer = OrderedDict()
            # parent GDB
            dico_layer["src_name"] = path.basename(src.GetName())
            # getting layer object
            layer = src.GetLayerByIndex(layer_idx)
            # layer globals
            li_layers_names.append(layer.GetName())
            dico_layer["title"] = georeader.get_title(layer)
            li_layers_idx.append(layer_idx)

            # features
            layer_feat_count = layer.GetFeatureCount()
            dico_layer["num_obj"] = layer_feat_count
            if layer_feat_count == 0:
                """ if layer doesn't have any object, return an error """
                dico_layer["error"] = "err_nobjet"
                self.alert = self.alert + 1
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
            dico_layer["EPSG"] = srs_details[1]
            dico_layer["srs_type"] = srs_details[2]

            # spatial extent
            extent = georeader.get_extent_as_tuple(layer)
            dico_layer["Xmin"] = extent[0]
            dico_layer["Xmax"] = extent[1]
            dico_layer["Ymin"] = extent[2]
            dico_layer["Ymax"] = extent[3]

            # storing layer into the GDB dictionary
            dico_dataset[
                "{0}_{1}".format(layer_idx, dico_layer.get("title"))
            ] = dico_layer
            # summing fields number
            total_fields += dico_layer.get("num_fields", 0)
            # summing objects number
            total_objs += dico_layer.get("num_obj", 0)
            # deleting dictionary to ensure having cleared space
            del dico_layer
        # storing fileds and objects sum
        dico_dataset["total_fields"] = total_fields
        dico_dataset["total_objs"] = total_objs

        # warnings messages
        if self.alert:
            dico_dataset["err_gdal"] = gdal_err.err_type, gdal_err.err_msg
        else:
            pass
        # clean exit
        del src


# ############################################################################
# #### Stand alone program #######
# ################################

if __name__ == "__main__":
    """ standalone execution for tests. Paths are relative considering a test
    within the official repository (https://github.com/Guts/DicoGIS/)"""
    from os import chdir

    # sample files
    chdir(r"..\..\test\datatest\FileGDB\Esri_FileGDB")
    # test text dictionary
    textos = OrderedDict()
    textos["srs_comp"] = "Compound"
    textos["srs_geoc"] = "Geocentric"
    textos["srs_geog"] = "Geographic"
    textos["srs_loca"] = "Local"
    textos["srs_proj"] = "Projected"
    textos["srs_vert"] = "Vertical"
    textos["geom_point"] = "Point"
    textos["geom_ligne"] = "Line"
    textos["geom_polyg"] = "Polygon"

    # searching for File GeoDataBase
    num_folders = 0
    li_gdb = [
        path.realpath(r"Points.gdb"),
        path.realpath(r"Polygons.gdb"),
        path.realpath(r"GDB_Test.gdb"),
        path.realpath(r"MulitNet_2015_12.gdb"),
    ]
    for root, dirs, files in walk(r"..\test\datatest"):
        num_folders = num_folders + len(dirs)
        for d in dirs:
            try:
                path.join(root, d)
                full_path = path.join(root, d)
            except UnicodeDecodeError as e:
                full_path = path.join(root, d.decode("latin1"))
                logger.error(full_path), e
            if full_path[-4:].lower() == ".gdb":
                # add complete path of shapefile
                li_gdb.append(path.abspath(full_path))
            else:
                pass

    # recipient datas
    dico_dataset = OrderedDict()
    gdbReader = ReadGDB()

    # read GDB
    for source_path in li_gdb:
        dico_dataset.clear()
        source_path = path.abspath(source_path)
        print(path.isdir(source_path), source_path)
        if path.isdir(source_path):
            print("\n{0}: ".format(path.realpath(source_path)))
            gdbReader.infos_dataset(
                source_path=source_path,
                dico_dataset=dico_dataset,
                txt=textos,
                tipo="Esri FileGDB",
            )
            # print results
            print(dico_dataset)
        else:
            print(path.isfile(source_path), source_path)
            pass
