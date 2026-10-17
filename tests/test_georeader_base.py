#! python3  # noqa: E265

"""
Usage from the repo root folder:
    python -m unittest tests.test_georeader_base
"""

# #############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import unittest

# 3rd party
from osgeo import ogr, osr

# package
from dicogis.georeaders.read_vector_flat_dataset import ReadVectorFlatDataset


# #############################################################################
# ########## Functions #############
# ##################################


def _memory_layer(
    spatial_ref: osr.SpatialReference,
) -> tuple[ogr.DataSource, ogr.Layer]:
    """Create an in-memory layer with the given spatial reference.

    The datasource is returned too: the layer is only valid while it lives.
    """
    datasource = ogr.GetDriverByName("Memory").CreateDataSource("srs_test")
    layer = datasource.CreateLayer("srs_test", srs=spatial_ref)
    return datasource, layer


# #############################################################################
# ########## Classes ###############
# ##################################


class TestGetSrsDetails(unittest.TestCase):
    """Test GeoReaderBase.get_srs_details()."""

    def setUp(self):
        self.georeader = ReadVectorFlatDataset()

    def test_epsg_crs_is_identified(self):
        spatial_ref = osr.SpatialReference()
        spatial_ref.ImportFromEPSG(2154)
        _datasource, layer = _memory_layer(spatial_ref)

        crs_name, crs_registry, crs_code, crs_type = self.georeader.get_srs_details(
            dataset_or_layer=layer
        )

        self.assertEqual(crs_name, "RGF93 v1 / Lambert-93")
        self.assertEqual((crs_registry, crs_code), ("EPSG", "2154"))
        self.assertEqual(crs_type, "srs_proj")

    def test_crs_without_epsg_equivalent_is_still_described(self):
        """A CRS that AutoIdentifyEPSG() can't match raises with GDAL exceptions
        enabled: the dataset must still be described, not dropped."""
        spatial_ref = osr.SpatialReference()
        spatial_ref.ImportFromProj4("+proj=ortho +lat_0=40 +lon_0=-5 +ellps=WGS84")
        _datasource, layer = _memory_layer(spatial_ref)

        crs_name, _crs_registry, _crs_code, crs_type = self.georeader.get_srs_details(
            dataset_or_layer=layer
        )

        self.assertEqual(crs_name, spatial_ref.GetName())
        self.assertEqual(crs_type, "srs_proj")


# #############################################################################
# ##### Main #######################
# ##################################
if __name__ == "__main__":
    unittest.main()
