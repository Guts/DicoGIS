#! python3

"""
Usage from the repo root folder:
    python -m unittest tests.test_georeader_vector_formats
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
from dicogis.georeaders.read_vector_flat_dataset import ReadVectorFlatDataset
from tests.fixtures.fixture_data_generator import generate_simple_vector_dataset


# #############################################################################
# ########## Globals ###############
# ##################################

# the Geoconcept driver is an optional/plugin OGR driver: some GDAL packaging
# (e.g. the ubuntugis-unstable PPA build used in CI) does not include it.
GEOCONCEPT_AVAILABLE = ogr.GetDriverByName("Geoconcept") is not None

# #############################################################################
# ########## Classes ###############
# ##################################


class TestReadVectorFlatDatasetFormats(unittest.TestCase):
    """Test ReadVectorFlatDataset.infos_dataset() against every single-layer
    flat vector format it is registered for in
    ProcessingFiles.MATRIX_FORMAT_GEOREADER, beyond shapefiles (already
    covered in test_infos_vector.py).

    Fixtures are generated on the fly with the matching OGR driver rather
    than downloaded, since some of these formats (MapInfo TAB, Geoconcept
    GXT) have no sample in the `gisdata`/`qgisdata` fixture sets used
    elsewhere in the suite.
    """

    def setUp(self):
        """Executed before each test."""
        self.tmp_dir = tempfile.TemporaryDirectory(
            prefix="DicoGIS_test_georeader_vector_formats_",
            ignore_cleanup_errors=True,
        )

    def tearDown(self):
        """Executed after each test."""
        self.tmp_dir.cleanup()

    def _assert_common_metadata(self, metadataset, fixture_path: Path) -> None:
        """Assertions shared by every format: a well-formed, error-free
        single-layer vector metadataset with the expected 5 point features.

        Feature attributes count is not asserted to a specific value here:
        some drivers (KML, GML) add their own extra fields (id, gml_id...)
        on top of the 2 fields the fixture defines.
        """
        self.assertTrue(metadataset.processing_succeeded is not False, fixture_path)
        self.assertEqual(metadataset.processing_error_msg, "", fixture_path)
        self.assertEqual(metadataset.features_objects_count, 5, fixture_path)
        self.assertIsInstance(
            metadataset.feature_attributes, (list, tuple), fixture_path
        )
        self.assertGreaterEqual(metadataset.count_feature_attributes, 1, fixture_path)
        self.assertIsInstance(metadataset.geometry_type, str, fixture_path)
        self.assertIn("point", metadataset.geometry_type.lower(), fixture_path)
        self.assertIsInstance(metadataset.bbox, tuple, fixture_path)
        self.assertIsInstance(metadataset.crs_name, str, fixture_path)
        self.assertIsInstance(metadataset.files_dependencies, list, fixture_path)
        self.assertEqual(metadataset.name, fixture_path.stem, fixture_path)

    # -- Tests ------------------------------------------------------------

    def test_read_mapinfo_tab(self):
        """MapInfo TAB files are read through ReadVectorFlatDataset."""
        fixture_path = generate_simple_vector_dataset(
            gdal_driver_name="MapInfo File",
            output_path=Path(self.tmp_dir.name, "parcels.tab"),
        )

        metadataset = ReadVectorFlatDataset().infos_dataset(
            fixture_path, fallback_format="MapInfo TAB"
        )

        self._assert_common_metadata(metadataset, fixture_path)
        self.assertEqual(metadataset.format_gdal_short_name, "MapInfo File")

    def test_read_kml(self):
        """KML files are read through ReadVectorFlatDataset."""
        fixture_path = generate_simple_vector_dataset(
            gdal_driver_name="KML",
            output_path=Path(self.tmp_dir.name, "trail.kml"),
        )

        metadataset = ReadVectorFlatDataset().infos_dataset(
            fixture_path, fallback_format="KML"
        )

        self._assert_common_metadata(metadataset, fixture_path)

    def test_read_gml(self):
        """GML files are read through ReadVectorFlatDataset."""
        fixture_path = generate_simple_vector_dataset(
            gdal_driver_name="GML",
            output_path=Path(self.tmp_dir.name, "network.gml"),
        )

        metadataset = ReadVectorFlatDataset().infos_dataset(
            fixture_path, fallback_format="GML"
        )

        self._assert_common_metadata(metadataset, fixture_path)
        self.assertEqual(metadataset.format_gdal_short_name, "GML")

    def test_read_geojson(self):
        """GeoJSON files are read through ReadVectorFlatDataset."""
        fixture_path = generate_simple_vector_dataset(
            gdal_driver_name="GeoJSON",
            output_path=Path(self.tmp_dir.name, "districts.geojson"),
        )

        metadataset = ReadVectorFlatDataset().infos_dataset(
            fixture_path, fallback_format="GeoJSON"
        )

        self._assert_common_metadata(metadataset, fixture_path)
        self.assertEqual(metadataset.format_gdal_short_name, "GeoJSON")

    @unittest.skipUnless(
        GEOCONCEPT_AVAILABLE,
        "GDAL was built without the optional Geoconcept driver.",
    )
    def test_read_gxt_geoconcept(self):
        """Geoconcept eXport Text (.gxt) files are read through
        ReadVectorFlatDataset."""
        fixture_path = generate_simple_vector_dataset(
            gdal_driver_name="Geoconcept",
            output_path=Path(self.tmp_dir.name, "survey.gxt"),
        )

        metadataset = ReadVectorFlatDataset().infos_dataset(
            fixture_path, fallback_format="Geoconcept"
        )

        self._assert_common_metadata(metadataset, fixture_path)
        self.assertEqual(metadataset.format_gdal_short_name, "Geoconcept")

    def test_read_nonexistent_file_is_reported_as_error(self):
        """A missing file is reported as a failed processing rather than
        raising, and falls back to the format passed as fallback_format."""
        fixture_path = Path(self.tmp_dir.name, "missing.geojson")

        metadataset = ReadVectorFlatDataset().infos_dataset(
            fixture_path, fallback_format="GeoJSON"
        )

        self.assertFalse(metadataset.processing_succeeded)
        self.assertEqual(metadataset.format_gdal_long_name, "GeoJSON")


# #############################################################################
# ##### Main #######################
# ##################################
if __name__ == "__main__":
    unittest.main()
