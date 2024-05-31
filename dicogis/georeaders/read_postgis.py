#! python3  # noqa: E265


# ############################################################################
# ######### Libraries #############
# #################################


# Standard library
import logging
from typing import Optional

# 3rd party libraries
from osgeo import gdal, ogr

# package
from dicogis.constants import GDAL_POSTGIS_OPEN_OPTIONS
from dicogis.georeaders.base_georeader import GeoReaderBase
from dicogis.models.database_connection import DatabaseConnection
from dicogis.models.metadataset import MetaDatabaseTable

# ############################################################################
# ######### Globals ############
# ##############################

# handling GDAL/OGR specific exceptions

logger = logging.getLogger(__name__)

# ############################################################################
# ######### Classes #############
# #################################


class ReadPostGIS(GeoReaderBase):
    """Read PostGIS database."""

    def __init__(
        self,
        # connection parameters
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
        self.conn: Optional[ogr.DataSource] = None
        self.counter_alerts = 0
        self.views_included = views_included

        # connection infos as attributes
        self.db_connection = DatabaseConnection(
            database_name=db_name,
            host=host,
            port=port,
            user_name=user,
            user_password=password,
            service_name=service,
            is_esri_sde=False,
            is_postgis=True,
        )

        super().__init__(dataset_type="sgbd_postgis")

    def get_connection(self) -> Optional[ogr.DataSource]:
        """Open a connection to the PostgreSQL database using GDAL.

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
                self.db_connection.pg_connection_string,
                gdal.OF_READONLY | gdal.OF_VECTOR | gdal.OF_VERBOSE_ERROR,
                open_options=gdal_open_options,
            )
            logger.info(
                f"Access granted: connecting people to {conn.GetLayerCount()} tables!"
            )
            self.db_connection.state_msg = "OK"
            self.conn = conn
            return conn
        except Exception as err:
            self.db_connection.state_msg = f"KO: {err}"
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
            self.db_connection.state_msg = "OK"
            return pgis_version
        except Exception as err:
            self.db_connection.state_msg = f"KO: {err}"
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
        metadataset: Optional[MetaDatabaseTable] = None,
    ) -> Optional[MetaDatabaseTable]:
        """Extract metadata from PostGIS layer and store it into the dictionary.

        Args:
            layer (ogr.Layer): input PostGIS layer
            dico_dataset (Optional[dict], optional): dictionary to fill with extracted \
                data. Defaults to None.
        """
        if metadataset is None:
            metadataset = MetaDatabaseTable(
                format_gdal_long_name=self.conn.GetDriver().LongName,
                format_gdal_short_name=self.conn.GetDriver().ShortName,
                database_connection=self.db_connection,
                dataset_type="sgbd_postgis",
            )

        # check layer type
        if not isinstance(layer, ogr.Layer):
            self.counter_alerts = self.counter_alerts + 1
            self.erratum(
                target_container=metadataset,
                src_dataset_layer=layer,
                err_msg="Not a OGR layer (no PostGIS table/view)",
            )
            logger.error(
                f"OGR: {layer} is not a valid OGR layer (no PostGIS table/view)."
            )
            return metadataset

        # sgbd info
        self.db_connection.sgbd_schemas = self.get_schemas()
        self.db_connection.sgbd_version = self.get_postgis_version()

        # layer name
        metadataset.name = layer.GetName()
        logger.info(f"Analyzing layer: {metadataset.name}")

        # raising forbidden access
        try:
            obj = layer.GetFeatureCount()  # get the first object
        except RuntimeError as err:
            if "permission denied" in str(err):
                mess = str(err).split("\n")[0]
                self.counter_alerts = self.counter_alerts + 1
                self.erratum(
                    target_container=metadataset, src_dataset_layer=layer, err_msg=mess
                )
                logger.error(f"GDAL: permission denied {layer.GetName()} - {mess}")
                return metadataset
            else:
                raise err

        except Exception as err:
            self.counter_alerts = self.counter_alerts + 1
            self.erratum(
                target_container=metadataset, src_dataset_layer=layer, err_msg=err
            )
            logger.error(f"Unable to count objects for {layer.GetName()}. Trace: {err}")

            return metadataset

        # schema name
        if "." in metadataset.name:
            metadataset.schema_name = metadataset.name.split(".")[0]

        # basic information
        # features
        metadataset.features_objects_count = layer.GetFeatureCount()
        if metadataset.features_objects_count == 0:
            """if layer doesn't have any object, return an error"""
            self.counter_alerts += 1
            self.erratum(
                target_container=metadataset,
                src_dataset_layer=layer,
                err_msg="err_nobjet",
            )
            return metadataset

        # fields
        layer_def = layer.GetLayerDefn()
        metadataset.feature_attributes = self.get_fields_details(
            ogr_layer_definition=layer_def
        )

        # geometry type
        layer_geom_type = self.get_geometry_type(layer)
        if layer_geom_type is None:
            metadataset.processing_error_msg += f"{self.gdal_err.err_msg} -- "
            metadataset.processing_error_type += f"{self.gdal_err.err_type} -- "
            metadataset.processing_succeeded = False
        metadataset.geometry_type = layer_geom_type

        # SRS
        srs_details = self.get_srs_details(layer)
        metadataset.crs_name = srs_details[0]
        metadataset.crs_registry_code = srs_details[1]
        metadataset.crs_type = srs_details[2]

        # spatial extent
        metadataset.bbox = self.get_extent_as_tuple(dataset_or_layer=layer)

        # warnings messages
        if self.counter_alerts:
            metadataset.processing_succeeded = False
            metadataset.processing_error_msg = self.gdal_err.err_msg
            metadataset.processing_error_type = self.gdal_err.err_type

        # clean exit
        del obj

        return metadataset
