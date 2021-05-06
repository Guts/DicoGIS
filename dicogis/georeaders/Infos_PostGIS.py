#! python3  # noqa: E265


# ----------------------------------------------------------------------------
# Name:         InfosOGR_PG
# Purpose:      Use GDAL/OGR library to extract informations about
#                   geographic data contained in a PostGIS database.
#                   It permits a more friendly use as submodule.
#
# Author:       Julien Moura (https://github.com/Guts/)
# ----------------------------------------------------------------------------

# ############################################################################
# ######### Libraries #############
# #################################

import logging

# Standard library
from collections import OrderedDict

# 3rd party libraries
try:
    from osgeo import gdal, ogr
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
youtils = Utils(ds_type="postgis")
logger = logging.getLogger(__name__)

# ############################################################################
# ######### Classes #############
# #################################


class ReadPostGIS:
    def __init__(
        self,
        host="localhost",
        port=5432,
        db_name="postgis",
        user="postgres",
        password="postgres",
        views_included=1,
        dico_dataset=OrderedDict(),
        txt=dict(),
    ):
        """Uses gdal/ogr functions to extract basic informations about
        geographic file (handles shapefile or MapInfo tables)
        and store into the dictionaries.

        layer = path to the geographic file
        dico_dataset = dictionary for global informations
        dico_fields = dictionary for the fields' informations
        tipo = feature type to read
        text = dictionary of texts to display
        """
        # handling GDAL/OGR specific exceptions
        gdal.AllRegister()
        ogr.UseExceptions()
        gdal.UseExceptions()

        # Creating variables
        self.dico_dataset = dico_dataset
        self.txt = txt
        self.alert = 0
        if views_included:
            gdal.SetConfigOption(str("PG_LIST_ALL_TABLES"), str("YES"))
            logger.info("PostgreSQL views enabled.")
        else:
            gdal.SetConfigOption(str("PG_LIST_ALL_TABLES"), str("NO"))
            logger.info("PostgreSQL views disabled.")

        # connection infos
        self.host = host
        self.port = port
        self.db_name = db_name
        self.user = user
        self.password = password
        self.conn_settings = "PG: host={} port={} dbname={} user={} password={}".format(
            host, port, db_name, user, password
        )

        # testing connection
        self.conn = self.get_connection()
        if not self.conn:
            self.alert += 1
            youtils.erratum(
                ctner=dico_dataset,
                mess_type=1,
                ds_lyr=self.conn_settings,
                mess="err_connection_failed",
            )
            dico_dataset["err_gdal"] = gdal_err.err_type, gdal_err.err_msg
            return None
        else:
            pass

        # sgbd info
        dico_dataset["sgbd_version"] = self.get_version()
        dico_dataset["sgbd_schemas"] = self.get_schemas()

    def get_connection(self):
        """TO DOC."""
        try:
            conn = ogr.Open(str(self.conn_settings))
            logging.info(
                "Access granted : connecting people to {} tables!".format(len(conn))
            )
            return conn
        except Exception as err:
            self.dico_dataset["conn_state"] = err
            logging.error("Connection failed. Check settings: {0}".format(str(err)))
            return 0

    def get_version(self):
        """TO DO."""
        sql = self.conn.ExecuteSQL(str("SELECT PostGIS_full_version();"))
        feat = sql.GetNextFeature()
        return feat.GetField(0)

    def get_schemas(self):
        """TO DO."""
        sql_schemas = str("select nspname from pg_catalog.pg_namespace;")
        return self.conn.ExecuteSQL(sql_schemas)

    def infos_dataset(self, layer, dico_dataset=dict(), tipo="PostGIS"):
        """TO DO."""
        if not dico_dataset:
            dico_dataset = self.dico_dataset
        else:
            pass
        # check layer type
        if type(layer) is not ogr.Layer:
            self.alert = self.alert + 1
            youtils.erratum(dico_dataset, layer, "Not a PostGIS layer")
            logging.error("OGR: {} - {}".format(layer, "Not a PostGIS layer."))
            return None
        else:
            dico_dataset["format"] = tipo
            pass

        # connection info
        dico_dataset["sgbd_host"] = self.host
        dico_dataset["sgbd_port"] = self.port
        dico_dataset["db_name"] = self.db_name
        dico_dataset["user"] = self.user
        dico_dataset["password"] = self.password
        dico_dataset["connection_string"] = self.conn_settings
        # sgbd info
        dico_dataset["sgbd_version"] = self.get_version()
        dico_dataset["sgbd_schemas"] = self.get_schemas()

        # layer name
        dico_dataset["name"] = layer.GetName()
        dico_dataset["title"] = layer.GetName().capitalize()
        logger.warning("Analyzing layer: {}".format(dico_dataset.get("name")))

        # raising forbidden access
        try:
            obj = layer.GetFeatureCount()  # get the first object
        except RuntimeError as e:
            if "permission denied" in str(e):
                mess = str(e).split("\n")[0]
                self.alert = self.alert + 1
                youtils.erratum(ctner=dico_dataset, ds_lyr=layer, mess=mess)
                logging.error("GDAL: {} - {}".format(layer.GetName(), mess))
                return None
            else:
                pass
        except Exception as err:
            logging.error(err)
            return None

        # schema name
        try:
            layer.GetName().split(".")[1]
            dico_dataset["folder"] = layer.GetName().split(".")[0]
        except IndexError:
            dico_dataset["folder"] = "public"

        # basic information
        # features
        layer_feat_count = layer.GetFeatureCount()
        dico_dataset["num_obj"] = layer_feat_count
        if layer_feat_count == 0:
            """if layer doesn't have any object, return an error"""
            self.alert += 1
            youtils.erratum(ctner=dico_dataset, ds_lyr=layer, mess="err_nobjet")
            return None
        else:
            pass

        # fields
        layer_def = layer.GetLayerDefn()
        dico_dataset["num_fields"] = layer_def.GetFieldCount()
        dico_dataset["fields"] = georeader.get_fields_details(layer_def)

        # geometry type
        dico_dataset["type_geom"] = georeader.get_geometry_type(layer)

        # SRS
        srs_details = georeader.get_srs_details(layer, self.txt)
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

        # clean exit
        del obj


# ############################################################################
# #### Stand alone program ########
# #################################

if __name__ == "__main__":
    """standalone execution for tests. Paths are relative considering a test
    within the official repository (https://github.com/Guts/DicoGIS/)"""
    # libraries import

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

    # PostGIS database settings
    test_host = "postgresql-guts.alwaysdata.net"
    test_db = "guts_gis"
    test_user = "guts_player"
    test_pwd = "letsplay"
    test_conn = "PG: host={} dbname={} user={} password={}".format(
        test_host, test_db, test_user, test_pwd
    )
    # use reader
    dico_dataset = OrderedDict()
    pgReader = ReadPostGIS(
        host=test_host,
        port=5432,
        db_name=test_db,
        user=test_user,
        password=test_pwd,
        views_included=1,
        dico_dataset=dico_dataset,
        txt=textos,
    )
    # check if connection succeeded
    if not pgReader.conn:
        # connection failed
        print(dico_dataset)
        exit()
    else:
        print("{} tables found.".format(len(pgReader.conn)))

    # parse layers
    for layer in pgReader.conn:
        dico_dataset.clear()
        print("\n", layer.GetName())
        pgReader.infos_dataset(layer)
        print(dico_dataset)
