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


# Standard library
import logging
from typing import Optional

# 3rd party libraries
import pgserviceparser
from osgeo import gdal, ogr

# package
from dicogis.georeaders.gdal_exceptions_handler import GdalErrorHandler
from dicogis.georeaders.geo_infos_generic import GeoInfosGenericReader
from dicogis.georeaders.geoutils import Utils

# ############################################################################
# ######### Globals ############
# ##############################

# handling GDAL/OGR specific exceptions
gdal.AllRegister()
ogr.UseExceptions()
gdal.UseExceptions()
gdal_err = GdalErrorHandler()
georeader = GeoInfosGenericReader()
youtils = Utils(ds_type="postgis")
logger = logging.getLogger(__name__)

# ############################################################################
# ######### Classes #############
# #################################


class ReadPostGIS:
    """Read PostGIS database."""

    def __init__(
        self,
        txt: dict,
        dico_dataset: dict,
        host: Optional[str] = None,
        port: Optional[int] = None,
        db_name: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        service: Optional[str] = None,
        views_included: bool = True,
    ):
        """Uses OGR to extract basic informations about geodata stored into a PostGIS
            database.

        Args:
            txt (dict): dictionary of translated texts
            dico_dataset (dict): _description_
            host (str, optional): postgres connection host. Defaults to "localhost".
            port (int, optional): postgres connection port. Defaults to 5432.
            db_name (str, optional): postgres database name. Defaults to "postgis".
            user (str, optional): postgres connection user name. Defaults to "postgres".
            password (str, optional): postgres connection user password. Defaults to \
                "postgres".
            service (Optional[str], optional): name of pg_service to use to connect to \
                the database. If defined, other connection parameters are ignored. \
                Defaults to None.
            views_included (bool, optional): option to include views. Defaults to True.
        """

        # Creating variables
        self.dico_dataset = dico_dataset
        self.txt = txt
        self.alert = 0
        if views_included:
            gdal.SetConfigOption("SKIP_VIEWS", "NO")
            logger.info("PostgreSQL views enabled.")
        else:
            gdal.SetConfigOption("SKIP_VIEWS", "YES")
            logger.info("PostgreSQL views disabled.")

        # connection infos as attributes
        self.host = host
        self.port = port
        self.db_name = db_name
        self.user = user
        self.password = password
        self.service = service

        # build connection string
        if isinstance(service, str) and service in pgserviceparser.service_names():
            self.conn_string = f"PG:service={service}"
        else:
            self.conn_string = (
                f"PG: host={host} port={port} dbname={db_name} "
                f"user={user} password={password}"
            )

        # testing connection
        self.conn = self.get_connection()
        if not self.conn:
            self.alert += 1
            youtils.erratum(
                ctner=dico_dataset,
                mess_type=1,
                ds_lyr=self.conn_string,
                mess="err_connection_failed",
            )
            dico_dataset["err_gdal"] = gdal_err.err_type, gdal_err.err_msg
        else:
            pass

        # sgbd info
        dico_dataset["sgbd_version"] = self.get_version()
        dico_dataset["sgbd_schemas"] = self.get_schemas()

    def get_connection(self):
        """TO DOC."""
        try:
            conn = ogr.Open(str(self.conn_string))
            logging.info(f"Access granted : connecting people to {len(conn)} tables!")
            return conn
        except Exception as err:
            self.dico_dataset["conn_state"] = err
            logging.error(f"Connection failed. Check settings: {str(err)}")
            return 0

    def get_version(self):
        """TO DO."""
        sql = self.conn.ExecuteSQL("SELECT PostGIS_full_version();")
        feat = sql.GetNextFeature()
        return feat.GetField(0)

    def get_schemas(self):
        """TO DO."""
        sql_schemas = "select nspname from pg_catalog.pg_namespace;"
        return self.conn.ExecuteSQL(sql_schemas)

    def infos_dataset(self, layer, dico_dataset={}, tipo="PostGIS"):
        """TO DO."""
        if not dico_dataset:
            dico_dataset = self.dico_dataset
        else:
            pass
        # check layer type
        if not isinstance(layer, ogr.Layer):
            self.alert = self.alert + 1
            youtils.erratum(dico_dataset, layer, "Not a PostGIS layer")
            logging.error("OGR: {} - {}".format(layer, "Not a PostGIS layer."))
            return None
        else:
            dico_dataset["format"] = tipo
            pass

        # connection info
        dico_dataset["pg_service"] = self.service
        dico_dataset["sgbd_host"] = self.host
        dico_dataset["sgbd_port"] = self.port
        dico_dataset["db_name"] = self.db_name
        dico_dataset["user"] = self.user
        dico_dataset["password"] = self.password
        dico_dataset["connection_string"] = self.conn_string
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
                logging.error(f"GDAL: {layer.GetName()} - {mess}")
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
    """Standalone execution for quick and dirty tests."""
    # test text dictionary
    textos = {
        "srs_comp": "Compound",
        "srs_geoc": "Geocentric",
        "srs_geog": "Geographic",
        "srs_loca": "Local",
        "srs_proj": "Projected",
        "srs_vert": "Vertical",
        "geom_point": "Point",
        "geom_ligne": "Line",
        "geom_polyg": "Polygon",
    }

    # PostGIS database settings
    test_host = "postgresql-guts.alwaysdata.net"
    test_db = "guts_gis"
    test_user = "guts_player"
    test_pwd = "letsplay"

    # use reader
    dico_dataset = {}
    pgReader = ReadPostGIS(
        # host=test_host,
        # port=5432,
        # db_name=test_db,
        # user=test_user,
        # password=test_pwd,
        service="dev_alwaysdata_reader",
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
        print(f"{len(pgReader.conn)} tables found.")

    # parse layers
    for layer in pgReader.conn:
        dico_dataset.clear()
        print("\n", layer.GetName())
        pgReader.infos_dataset(layer)
        print(dico_dataset)
