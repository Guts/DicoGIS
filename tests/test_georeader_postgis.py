#! python3

"""
Usage from the repo root folder:

    python -m unittest tests.test_georeader_postgis
"""

# #############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import unittest
from os import environ, unsetenv
from pathlib import Path

# 3rd party
from osgeo import gdal

# package
from dicogis.georeaders.read_postgis import ReadPostGIS
from dicogis.models.metadataset import MetaDatabaseTable, MetaDataset

# #############################################################################
# ########## Classes ###############
# ##################################


class TestGeoReaderPostgis(unittest.TestCase):
    """Test info extractor for PostGIS datasets."""

    @classmethod
    def setUpClass(cls):
        # fixtures
        cls.pg_connection_string = "PG:service=dicogis_test"
        cls.fixture_pgservice_conf = Path("tests/fixtures/database/pg_service.conf")
        cls.fixture_good_vector = Path("tests/fixtures/gisdata/data/good/vector/")
        assert cls.fixture_pgservice_conf.exists(), (
            "The required fixture pg_service.conf file is missing: "
            f"{cls.fixture_pgservice_conf}"
        )
        cls.textos = {
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
        # check connection
        environ["PGSERVICEFILE"] = f"{cls.fixture_pgservice_conf.resolve()}"
        pg_conn: gdal.Dataset = gdal.OpenEx(
            "PG:service=dicogis_test",
            gdal.OF_VECTOR | gdal.OF_VERBOSE_ERROR,
        )

        pg_conn.ExecuteSQL("CREATE SCHEMA IF NOT EXISTS dicogis_unittests;")

        cls.commented_table_comment = "A table with a comment for tests purposes."
        cls.commented_table_name = None

        # load shapefiles to PostGIS
        gdal.SetConfigOption("PG_USE_COPY", "YES")
        for shapefile in cls.fixture_good_vector.glob("**/*.shp"):
            print(f"Loading {shapefile} into tests database.")
            # Open the Shapefile
            src_shp: gdal.Dataset = gdal.OpenEx(
                f"{shapefile.resolve()}", gdal.OF_READONLY | gdal.OF_VECTOR
            )
            if src_shp is None:
                print(f"Failed to open {shapefile}.")
                continue
            # Options for VectorTranslate
            options = gdal.VectorTranslateOptions(
                accessMode="overwrite",
                format="PostgreSQL",
                layerName=f"dicogis_unittests.{shapefile.stem}",
                skipFailures=True,
            )

            # Load the Shapefile into the PostGIS database
            gdal.VectorTranslate(
                destNameOrDestDS=cls.pg_connection_string,
                srcDS=src_shp,
                options=options,
            )

            if cls.commented_table_name is None:
                cls.commented_table_name = f"dicogis_unittests.{shapefile.stem}"

        # set a comment on one table, to test comment retrieval
        if cls.commented_table_name is not None:
            pg_conn.ExecuteSQL(
                f"COMMENT ON TABLE {cls.commented_table_name} IS "
                f"'{cls.commented_table_comment}';"
            )

    @classmethod
    def tearDownClass(cls) -> None:
        """Executed just before the test module is shutdown."""
        # clean up database
        pg_conn = gdal.OpenEx(
            "PG:service=dicogis_test",
            gdal.OF_VECTOR | gdal.OF_VERBOSE_ERROR,
        )

        pg_conn.ExecuteSQL("DROP SCHEMA IF EXISTS dicogis_tests CASCADE;")
        # rm custom environment variable
        unsetenv("PGSERVICEFILE")

    # -- TESTS --

    def test_postgis_reader(self):
        """Test PostGIS Georeader."""
        pg_reader = ReadPostGIS(service="dicogis_test")
        pg_reader.get_connection()
        self.assertIsInstance(pg_reader.get_postgis_version(), str)
        pg_schemas = pg_reader.get_schemas()
        self.assertIsInstance(pg_schemas, set, type(pg_schemas))
        self.assertIn("dicogis_unittests", pg_schemas)

        print(
            f"{pg_reader.conn.GetLayerCount()} tables found in "
            f"{pg_reader.conn.GetDescription()}."
        )

        # parse layers
        for idx_layer in range(pg_reader.conn.GetLayerCount()):
            layer = pg_reader.conn.GetLayerByIndex(idx_layer)
            metadaset = pg_reader.infos_dataset(layer=layer)
            self.assertIsInstance(metadaset, MetaDatabaseTable)
            self.assertIsInstance(metadaset, MetaDataset)

    def test_postgis_reader_relation_comment(self):
        """Test that a PostgreSQL relation's comment (COMMENT ON TABLE) is retrieved
        and stored into the metadataset description."""
        pg_reader = ReadPostGIS(service="dicogis_test")
        pg_reader.get_connection()

        relations_comments = pg_reader.get_relations_comments()
        self.assertIsInstance(relations_comments, dict)
        self.assertEqual(
            relations_comments.get(self.commented_table_name),
            self.commented_table_comment,
        )

        commented_layer = pg_reader.conn.GetLayerByName(self.commented_table_name)
        metadaset = pg_reader.infos_dataset(layer=commented_layer)
        self.assertEqual(metadaset.description, self.commented_table_comment)
