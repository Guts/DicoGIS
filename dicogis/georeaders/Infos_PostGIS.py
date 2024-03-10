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
from dicogis.constants import GDAL_POSTGIS_OPEN_OPTIONS
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
            dico_dataset (dict): dictionary where to store extracted metadata.
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
        self.views_included = views_included

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
            return

        # sgbd info
        dico_dataset["sgbd_version"] = self.get_postgis_version()
        dico_dataset["sgbd_schemas"] = self.get_schemas()

    def get_connection(self) -> Optional[ogr.DataSource]:
        """Returns OGR connection to the PostgreSQL database.

        Returns:
            Optional[ogr.DataSource]: OGR connection
        """
        gdal_open_options = GDAL_POSTGIS_OPEN_OPTIONS
        if self.views_included:
            gdal_open_options.append("SKIP_VIEWS=NO")
            logger.info("PostgreSQL views enabled.")
        else:
            gdal_open_options.append("SKIP_VIEWS=YES")
            logger.info("PostgreSQL views disabled.")

        try:
            conn: gdal.Dataset = gdal.OpenEx(
                str(self.conn_string),
                gdal.OF_READONLY | gdal.OF_VECTOR | gdal.OF_VERBOSE_ERROR,
                open_options=gdal_open_options,
            )
            logger.info(
                f"Access granted: connecting people to {conn.GetLayerCount()} tables!"
            )
            return conn
        except Exception as err:
            self.dico_dataset["conn_state"] = err
            logger.error(f"Connection failed. Check settings. Trace: {err}")
            return None

    def get_postgis_version(self) -> Optional[str]:
        """Returns the version of PostGIS extension.

        Returns:
            Optional[str]: PostGIS version
        """
        try:
            sql: ogr.Layer = self.conn.ExecuteSQL("SELECT PostGIS_full_version();")
            pgis_version: ogr.Feature = sql.GetNextFeature()
            pgis_version = pgis_version.GetFieldAsString(0)
            logger.debug(f"PostGIS full version: {pgis_version}")
            return pgis_version
        except Exception as err:
            self.dico_dataset["conn_state"] = err
            logger.error(f"Trying to retrieve PostGIS versions failed. Trace: {err}")
            return None

    def get_schemas(self) -> set[str]:
        """Return unique set of schemas names accessible by the logged user.

        Returns:
            set[str]: set of schemas names
        """
        sql_schemas = "select nspname from pg_catalog.pg_namespace;"
        pg_schemas: ogr.Layer = self.conn.ExecuteSQL(sql_schemas)
        return {feature["nspname"] for feature in pg_schemas}

    def infos_dataset(
        self,
        layer: ogr.Layer,
        dico_dataset: Optional[dict] = None,
    ) -> None:
        """Extract metadata from PostGIS layer and store it into the dictionary.

        Args:
            layer (ogr.Layer): input PostGIS layer
            dico_dataset (Optional[dict], optional): dictionary to fill with extracted \
                data. Defaults to None.
        """
        if dico_dataset is None:
            dico_dataset = self.dico_dataset

        # check layer type
        if not isinstance(layer, ogr.Layer):
            self.alert = self.alert + 1
            youtils.erratum(
                dico_dataset, layer, "Not a OGR layer (no PostGIS table/view)"
            )
            logger.error(
                f"OGR: {layer} is not a valid OGR layer (no PostGIS table/view)."
            )
            return None
        else:
            dico_dataset["format"] = "PostGIS"

        # connection info
        dico_dataset["pg_service"] = self.service
        dico_dataset["sgbd_host"] = self.host
        dico_dataset["sgbd_port"] = self.port
        dico_dataset["db_name"] = self.db_name
        dico_dataset["user"] = self.user
        dico_dataset["password"] = self.password
        dico_dataset["connection_string"] = self.conn_string
        # sgbd info
        dico_dataset["sgbd_version"] = self.get_postgis_version()
        dico_dataset["sgbd_schemas"] = self.get_schemas()

        # layer name
        dico_dataset["name"] = layer.GetName()
        dico_dataset["title"] = layer.GetName().capitalize()
        logger.info("Analyzing layer: {}".format(dico_dataset.get("name")))

        # raising forbidden access
        try:
            obj = layer.GetFeatureCount()  # get the first object
        except RuntimeError as err:
            if "permission denied" in str(err):
                mess = str(err).split("\n")[0]
                self.alert = self.alert + 1
                youtils.erratum(ctner=dico_dataset, ds_lyr=layer, mess=mess)
                logger.error(f"GDAL: permission denied {layer.GetName()} - {mess}")
                return None
            else:
                raise err

        except Exception as err:
            logger.error(f"Unable to count objects for {layer.GetName()}. Trace: {err}")
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

        # clean exit
        del obj
