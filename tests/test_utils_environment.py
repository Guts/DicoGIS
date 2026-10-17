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
import sys
import unittest
from unittest.mock import patch

# 3rd party
from packaging.version import parse

# project
from dicogis.utils.environment import (
    _command_output,
    get_available_gdal_drivers,
    get_gdal_version,
    get_proj_version,
    is_format_supported_by_gdal,
)


# ############################################################################
# ########## Classes #############
# ################################


class TestCommandOutput(unittest.TestCase):
    """Test the helper running command-line tools."""

    def test_missing_tool_returns_none(self):
        self.assertIsNone(_command_output("definitely-not-an-installed-tool"))

    def test_output_is_stripped(self):
        with patch(
            "dicogis.utils.environment.shutil.which", return_value=sys.executable
        ):
            output = _command_output("python", "-c", "print('  3.8.4  ')")

        self.assertEqual(output, "3.8.4")

    def test_stderr_only_when_asked(self):
        """proj prints its version on standard error."""
        script = "import sys; sys.stderr.write('Rel. 9.4.0')"
        with patch(
            "dicogis.utils.environment.shutil.which", return_value=sys.executable
        ):
            self.assertEqual(_command_output("python", "-c", script), "")
            self.assertEqual(
                _command_output("python", "-c", script, merge_stderr=True),
                "Rel. 9.4.0",
            )

    def test_failing_tool_returns_none(self):
        with patch(
            "dicogis.utils.environment.shutil.which", return_value=sys.executable
        ):
            self.assertIsNone(_command_output("python", "-c", "raise SystemExit(1)"))


class TestGdalVersionFromCommandLine(unittest.TestCase):
    """Test get_gdal_version() when the GDAL Python bindings are missing."""

    def _version_from(self, gdalinfo_output: str | None) -> str:
        with (
            patch("dicogis.utils.environment.GDAL_IS_AVAILABLE", False),
            patch(
                "dicogis.utils.environment._command_output",
                side_effect=lambda *args, **kwargs: (
                    gdalinfo_output if args[0] == "gdalinfo" else None
                ),
            ),
        ):
            return get_gdal_version()

    def test_two_digits_minor_version(self):
        """A fixed slice of the output used to return "3.10." here."""
        self.assertEqual(
            self._version_from("GDAL 3.10.1, released 2025/01/08"), "3.10.1"
        )

    def test_one_digit_minor_version(self):
        self.assertEqual(self._version_from("GDAL 3.8.4, released 2024/02/08"), "3.8.4")


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
