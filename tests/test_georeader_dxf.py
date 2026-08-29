#! python3

"""
Usage from the repo root folder:
    python -m unittest tests.test_georeader_dxf
"""

# #############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import tempfile
import unittest
from pathlib import Path

# package
from dicogis.georeaders.read_dxf import ReadCadDxf
from dicogis.models.metadataset import MetaVectorDataset
from tests.fixtures.fixture_data_generator import generate_simple_vector_dataset

# #############################################################################
# ########## Classes ###############
# ##################################


class TestReadCadDxf(unittest.TestCase):
    """Test info extractor for DXF (CAD) datasets."""

    def setUp(self):
        """Executed before each test."""
        self.tmp_dir = tempfile.TemporaryDirectory(
            prefix="DicoGIS_test_georeader_dxf_", ignore_cleanup_errors=True
        )

    def tearDown(self):
        """Executed after each test."""
        self.tmp_dir.cleanup()

    # -- Tests ------------------------------------------------------------

    def test_read_dxf(self):
        """A DXF file is read as a single-layer vector dataset (its one and
        only "entities" layer). DXF layers do not support arbitrary field
        creation, so the fixture is generated without extra attributes."""
        fixture_path = generate_simple_vector_dataset(
            gdal_driver_name="DXF",
            output_path=Path(self.tmp_dir.name, "plan.dxf"),
            layer_name="entities",
            with_attributes=False,
        )

        metadataset = ReadCadDxf().infos_dataset(
            fixture_path, fallback_format="AutoCAD DXF"
        )

        self.assertIsInstance(metadataset, MetaVectorDataset)
        self.assertEqual(metadataset.dataset_type, "flat_cad")
        self.assertTrue(metadataset.processing_succeeded is not False)
        self.assertEqual(metadataset.features_objects_count, 5)
        self.assertIsInstance(metadataset.geometry_type, str)
        self.assertIsInstance(metadataset.bbox, tuple)
        self.assertEqual(metadataset.format_gdal_short_name, "DXF")
        self.assertEqual(metadataset.name, fixture_path.stem)

    def test_read_nonexistent_dxf_is_reported_as_error(self):
        """A missing DXF file is reported as a failed processing rather than
        raising."""
        fixture_path = Path(self.tmp_dir.name, "missing.dxf")

        metadataset = ReadCadDxf().infos_dataset(
            fixture_path, fallback_format="AutoCAD DXF"
        )

        self.assertFalse(metadataset.processing_succeeded)


# #############################################################################
# ##### Main #######################
# ##################################
if __name__ == "__main__":
    unittest.main()
