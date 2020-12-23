#! python3  # noqa: E265

"""
    Name:         InfosSHP
    Purpose:      Use GDAL/OGR library to extract informations about
                       geographic data. It permits a more friendly use as
                       submodule.

    Author:       Julien Moura (https://github.com/Guts/)
"""

# ############################################################################
# ######### Libraries #############
# #################################

# Standard library
import logging
from collections import OrderedDict
from os import path
from time import localtime, strftime

# 3rd party libraries
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
except ImportError:
    from gdal_exceptions_handler import GdalErrorHandler
    from geo_infos_generic import GeoInfosGenericReader
    from geoutils import Utils

# ############################################################################
# ######### Globals ############
# ##############################

gdal_err = GdalErrorHandler()
georeader = GeoInfosGenericReader()
logger = logging.getLogger(__name__)
youtils = Utils("flat")

# ############################################################################
# ######### Classes #############
# ###############################


class ReadVectorFlatDataset:
    def __init__(self):
        """Class constructor."""
        # handling ogr specific exceptions
        errhandler = gdal_err.handler
        gdal.PushErrorHandler(errhandler)
        gdal.UseExceptions()
        ogr.UseExceptions()
        self.alert = 0

    def infos_dataset(
        self, source_path: str, dico_dataset, txt: dict = dict(), tipo=None
    ):
        """Use OGR functions to extract basic informations about
        geographic vector file (handles shapefile or MapInfo tables)
        and store into dictionaries.

        source_path = path to the geographic file
        dico_dataset = dictionary for global informations
        tipo = format
        txt = dictionary of text in the selected language
        """
        # changing working directory to layer folder
        # chdir(path.dirname(source_path))

        # raising corrupt files
        try:
            src = gdal.OpenEx(source_path, 0)  # GDAL driver
            if not tipo:
                dico_dataset["format"] = src.GetDriver().LongName
            else:
                dico_dataset["format"] = tipo
                pass
        except Exception as e:
            logger.error(e)
            self.alert = self.alert + 1
            dico_dataset["format"] = tipo
            youtils.erratum(dico_dataset, source_path, "err_corrupt")
            dico_dataset["err_gdal"] = gdal_err.err_type, gdal_err.err_msg
            return 0

        # raising incompatible files
        if not src:
            """ if file is not compatible """
            self.alert += 1
            dico_dataset["err_gdal"] = gdal_err.err_type, gdal_err.err_msg
            youtils.erratum(dico_dataset, source_path, "err_nobjet")
            return 0
        else:
            layer = src.GetLayer()  # get the layer
            pass

        # dataset name, title and parent folder
        try:
            dico_dataset["name"] = path.basename(source_path)
            dico_dataset["folder"] = path.dirname(source_path)
        except AttributeError as err:
            logger.warning(err)
            dico_dataset["name"] = path.basename(layer.GetName())
            dico_dataset["folder"] = path.dirname(layer.GetName())
        dico_dataset["title"] = (
            dico_dataset.get("name")[:-4].replace("_", " ").capitalize()
        )

        # dependencies and total size
        dependencies = youtils.list_dependencies(source_path, "auto")
        dico_dataset["dependencies"] = dependencies
        dico_dataset["total_size"] = youtils.sizeof(source_path, dependencies)
        # Getting basic dates
        crea, up = path.getctime(source_path), path.getmtime(source_path)
        dico_dataset["date_crea"] = strftime("%Y/%m/%d", localtime(crea))
        dico_dataset["date_actu"] = strftime("%Y/%m/%d", localtime(up))

        # features
        layer_feat_count = layer.GetFeatureCount()
        dico_dataset["num_obj"] = layer_feat_count
        if layer_feat_count == 0:
            """ if layer doesn't have any object, return an error """
            self.alert += 1
            youtils.erratum(dico_dataset, source_path, "err_nobjet")
            return 0
        else:
            pass

        # fields
        layer_def = layer.GetLayerDefn()
        dico_dataset["num_fields"] = layer_def.GetFieldCount()
        dico_dataset["fields"] = georeader.get_fields_details(layer_def)

        # geometry type
        dico_dataset["type_geom"] = georeader.get_geometry_type(layer)

        # SRS
        srs_details = georeader.get_srs_details(layer, txt)
        dico_dataset["srs"] = srs_details[0]
        dico_dataset["epsg"] = srs_details[1]
        dico_dataset["srs_type"] = srs_details[2]

        # spatial extent
        extent = georeader.get_extent_as_tuple(layer)
        dico_dataset["xmin"] = extent[0]
        dico_dataset["xmax"] = extent[1]
        dico_dataset["ymin"] = extent[2]
        dico_dataset["ymax"] = extent[3]

        # warnings messages
        if self.alert:
            dico_dataset["err_gdal"] = gdal_err.err_type, gdal_err.err_msg
        else:
            pass

        # clean & exit
        del src
        return 1, dico_dataset


# ############################################################################
# #### Stand alone program ########
# ################################

if __name__ == "__main__":
    """standalone execution for tests. Paths are relative considering a test
    within the official repository (https://github.com/Guts/DicoGIS)"""
    # libraries import
    # from os import getcwd
    vectorReader = ReadVectorFlatDataset()
    # test files
    li_vectors = [
        path.realpath(r"..\..\test\datatest\vectors\shp\itineraires_rando.shp"),
        path.realpath(r"..\..\test\datatest\vectors\shp\airports.shp"),
        path.realpath(r"..\..\test\datatest\vectors\tab\tab\airports_MI.tab"),
        path.realpath(r"..\..\test\datatest\vectors\tab\tab\Hydrobiologie.TAB"),
        path.realpath(r"..\..\test\datatest\vectors\geojson\airports.geojson"),
        path.realpath(r"..\..\test\datatest\vectors\gml\airports.gml"),
        path.realpath(r"..\..\test\datatest\vectors\kml\wc2014_MapTour.kml"),
        path.realpath(r"..\..\test\datatest\vectors\kml\PPRI_Loire_sept2014.kmz"),
    ]
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
    # recipient datas
    dico_dataset = OrderedDict()  # dictionary where will be stored info
    # execution
    for vector in li_vectors:
        """ looping on shapefiles list """
        # reset recipient data
        dico_dataset.clear()
        # getting the informations
        print("\n{0}".format(vector))
        info_ds = vectorReader.infos_dataset(
            path.abspath(vector), dico_dataset, txt=textos
        )
        print(info_ds)
