#! python3

"""
Usage from the repo root folder:
    python -m unittest tests.test_georeader_flat_database
"""

# #############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import tempfile
import unittest
from pathlib import Path

# 3rd party
from osgeo import ogr

# package
from dicogis.georeaders.read_vector_flat_geodatabase import ReadFlatDatabase
from dicogis.models.metadataset import MetaDatabaseFlat
from tests.fixtures.fixture_data_generator import (
    generate_simple_vector_dataset,
    spatial_ref,
)

# #############################################################################
# ########## Globals ###############
# ##################################

FILEGDB_AVAILABLE = bool(
    (driver := ogr.GetDriverByName("OpenFileGDB"))
    and driver.TestCapability(ogr.ODrCCreateDataSource)
)


def _make_multilayer_dataset(
    gdal_driver_name: str,
    output_path: Path,
    layers_features_count: dict[str, int],
    datasource_creation_options: list[str] | None = None,
) -> Path:
    """Create a dataset with one layer per (name, features_count) pair,
    each layer with a single integer field ('id') and point geometries."""
    driver: ogr.Driver = ogr.GetDriverByName(gdal_driver_name)
    output_path.parent.mkdir(exist_ok=True, parents=True)

    data_source: ogr.DataSource = driver.CreateDataSource(
        f"{output_path.resolve()}", options=datasource_creation_options or []
    )
    for layer_name, features_count in layers_features_count.items():
        layer: ogr.Layer = data_source.CreateLayer(
            layer_name, spatial_ref, geom_type=ogr.wkbPoint
        )
        layer.CreateField(ogr.FieldDefn("id", ogr.OFTInteger))
        for i in range(features_count):
            feature = ogr.Feature(layer.GetLayerDefn())
            feature.SetField("id", i)
            point = ogr.Geometry(ogr.wkbPoint)
            point.AddPoint_2D(float(i), float(i))
            feature.SetGeometry(point)
            layer.CreateFeature(feature)
            feature.Destroy()

    data_source.FlushCache()
    data_source = None
    return output_path


# #############################################################################
# ########## Classes ###############
# ##################################


class TestReadFlatDatabase(unittest.TestCase):
    """Test info extractor for flat databases: GeoPackage, Spatialite and
    Esri FileGeodatabase, all read through the multi-layer branch of
    ReadVectorFlatDataset.infos_dataset() (dataset_type='flat_database')."""

    def setUp(self):
        """Executed before each test."""
        self.tmp_dir = tempfile.TemporaryDirectory(
            prefix="DicoGIS_test_georeader_flat_database_",
            ignore_cleanup_errors=True,
        )

    def tearDown(self):
        """Executed after each test."""
        self.tmp_dir.cleanup()

    # -- Tests ------------------------------------------------------------

    def test_read_geopackage_single_layer(self):
        """A GeoPackage with a single layer is read with its layer details
        populated."""
        fixture_path = generate_simple_vector_dataset(
            gdal_driver_name="GPKG",
            output_path=Path(self.tmp_dir.name, "catalog.gpkg"),
            layer_name="places",
        )

        metadataset = ReadFlatDatabase().infos_dataset(fixture_path)

        self.assertIsInstance(metadataset, MetaDatabaseFlat)
        self.assertEqual(metadataset.count_layers, 1)
        layer_metadataset = metadataset.layers[0]
        self.assertEqual(layer_metadataset.name, "places")
        self.assertEqual(layer_metadataset.features_objects_count, 5)
        self.assertEqual(layer_metadataset.count_feature_attributes, 2)
        self.assertIn("point", layer_metadataset.geometry_type.lower())

    def test_read_geopackage_multiple_layers(self):
        """A GeoPackage with several layers gets every layer listed, and
        cumulated counts sum across all of them."""
        fixture_path = _make_multilayer_dataset(
            gdal_driver_name="GPKG",
            output_path=Path(self.tmp_dir.name, "multi.gpkg"),
            layers_features_count={"roads": 3, "buildings": 2},
        )

        metadataset = ReadFlatDatabase().infos_dataset(fixture_path)

        self.assertEqual(metadataset.count_layers, 2)
        self.assertEqual(
            {layer.name for layer in metadataset.layers}, {"roads", "buildings"}
        )
        self.assertEqual(metadataset.cumulated_count_feature_objects, 5)
        self.assertEqual(metadataset.cumulated_count_feature_attributes, 2)

    def test_read_spatialite(self):
        """A Spatialite database is read the same way as a GeoPackage."""
        fixture_path = generate_simple_vector_dataset(
            gdal_driver_name="SQLite",
            output_path=Path(self.tmp_dir.name, "catalog.sqlite"),
            layer_name="places",
            datasource_creation_options=["SPATIALITE=YES"],
        )

        metadataset = ReadFlatDatabase().infos_dataset(fixture_path)

        self.assertEqual(metadataset.count_layers, 1)
        self.assertEqual(metadataset.layers[0].features_objects_count, 5)

    @unittest.skipUnless(
        FILEGDB_AVAILABLE,
        "GDAL's OpenFileGDB driver does not support dataset creation "
        "(write support was added in GDAL 3.6).",
    )
    def test_read_esri_filegdb(self):
        """An Esri FileGeodatabase (created with the OpenFileGDB driver) is
        read the same way as a GeoPackage or Spatialite database."""
        fixture_path = generate_simple_vector_dataset(
            gdal_driver_name="OpenFileGDB",
            output_path=Path(self.tmp_dir.name, "catalog.gdb"),
            layer_name="places",
        )

        metadataset = ReadFlatDatabase().infos_dataset(fixture_path)

        self.assertEqual(metadataset.count_layers, 1)
        self.assertEqual(metadataset.layers[0].features_objects_count, 5)
        self.assertEqual(metadataset.format_gdal_short_name, "OpenFileGDB")

    def test_read_nonexistent_database_is_reported_as_error(self):
        """A missing database file is reported as a failed processing rather
        than raising."""
        fixture_path = Path(self.tmp_dir.name, "missing.gpkg")

        metadataset = ReadFlatDatabase().infos_dataset(
            fixture_path, fallback_format="GPKG"
        )

        self.assertFalse(metadataset.processing_succeeded)


# #############################################################################
# ##### Main #######################
# ##################################
if __name__ == "__main__":
    unittest.main()
