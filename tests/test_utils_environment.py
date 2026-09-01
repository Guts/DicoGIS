#! python3  # noqa E265

"""
Usage from the repo root folder:

.. code-block:: bash
    # for whole tests
    python -m unittest tests.test_utils_environment
    # for specific test
    python -m unittest tests.test_utils_environment.TestUtilsEnvironment.test_gdal_version
"""

# standard
import unittest
from unittest.mock import patch

# 3rd party
from packaging.version import parse

# project
from dicogis.utils.environment import (
    get_available_gdal_drivers,
    get_gdal_version,
    get_proj_version,
    is_format_supported_by_gdal,
)


# ############################################################################
# ########## Classes #############
# ################################


class TestUtilsEnvironment(unittest.TestCase):
    """Test envirpnment utils."""

    def test_gdal_version(self):
        """Test GDAL version retriever."""
        gdal_version = get_gdal_version()
        if not gdal_version.endswith("*"):
            self.assertTrue(parse(get_gdal_version()))

    def test_proj_version(self):
        """Test PROJ version retriever."""
        proj_version = get_proj_version()
        if proj_version:
            self.assertTrue(parse(proj_version))


class TestGetAvailableGdalDrivers(unittest.TestCase):
    """Test get_available_gdal_drivers()."""

    def test_returns_a_non_empty_set_of_driver_short_names(self):
        """GDAL is a required test dependency, so at least the always-core
        drivers (ESRI Shapefile, GTiff) must be reported."""
        drivers = get_available_gdal_drivers()
        self.assertIsInstance(drivers, frozenset)
        self.assertIn("ESRI Shapefile", drivers)
        self.assertIn("GTiff", drivers)

    @patch("dicogis.utils.environment.GDAL_IS_AVAILABLE", False)
    def test_returns_empty_set_when_gdal_unavailable(self):
        self.assertEqual(get_available_gdal_drivers(), frozenset())


class TestIsFormatSupportedByGdal(unittest.TestCase):
    """Test is_format_supported_by_gdal()."""

    def test_unknown_format_defaults_to_supported(self):
        """A format name absent from FORMAT_TO_GDAL_DRIVERS has nothing to
        gate on, so it is reported as supported."""
        self.assertTrue(is_format_supported_by_gdal("not_a_real_format", frozenset()))

    def test_format_with_no_matching_driver_is_unsupported(self):
        self.assertFalse(is_format_supported_by_gdal("geojson", frozenset()))

    def test_format_with_a_matching_driver_is_supported(self):
        self.assertTrue(is_format_supported_by_gdal("geojson", frozenset({"GeoJSON"})))

    def test_format_with_alternative_drivers_matches_any_one_of_them(self):
        """kml accepts either LIBKML or the older KML driver."""
        self.assertTrue(is_format_supported_by_gdal("kml", frozenset({"KML"})))
        self.assertTrue(is_format_supported_by_gdal("kml", frozenset({"LIBKML"})))
        self.assertFalse(is_format_supported_by_gdal("kml", frozenset({"GML"})))

    def test_defaults_to_the_real_driver_registry_when_not_given_one(self):
        """Called on the actual (GDAL-installed) test environment, at least
        shapefiles must be reported as supported."""
        self.assertTrue(is_format_supported_by_gdal("esri_shapefile"))


# ############################################################################
# ####### Stand-alone run ########
# ################################
if __name__ == "__main__":
    unittest.main()
