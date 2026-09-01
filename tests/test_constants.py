#! python3  # noqa E265

"""
Usage from the repo root folder:
    python -m unittest tests.test_constants
"""

# standard library
import unittest

# project
from dicogis.constants import (
    FORMAT_TO_GDAL_DRIVERS,
    SUPPORTED_FORMATS,
    FormatsRaster,
    FormatsVector,
)


# ############################################################################
# ########## Classes #############
# ################################


class TestSupportedFormats(unittest.TestCase):
    """Test the enums listing the formats DicoGIS supports."""

    def test_no_duplicated_extension(self):
        """Two members sharing a value become aliases in an Enum: the second one
        stops existing as a member of its own, disappears from iteration (hence
        from SUPPORTED_FORMATS and from the CLI's default --formats list) and
        resolves to the first one. `gxt` used to be declared as ".gml", which
        silently turned it into an alias of `gml`.
        """
        for enum_class in (FormatsVector, FormatsRaster):
            with self.subTest(enum=enum_class.__name__):
                # __members__ is what exposes aliases: iterating the enum itself
                # already skips them, so it would never see the duplicate
                extensions = [
                    member.value for member in enum_class.__members__.values()
                ]
                self.assertCountEqual(
                    extensions,
                    set(extensions),
                    f"{enum_class.__name__} has members sharing the same extension, "
                    "which makes them aliases instead of distinct formats",
                )

    def test_no_member_is_an_alias(self):
        """Every declared member must be its own member, not an alias of another
        one: aliases are skipped when iterating over the enum.
        """
        for enum_class in (FormatsVector, FormatsRaster):
            for name, member in enum_class.__members__.items():
                with self.subTest(enum=enum_class.__name__, member=name):
                    self.assertEqual(
                        member.name,
                        name,
                        f"{enum_class.__name__}.{name} is an alias of "
                        f"{member.name}: check its value for a duplicate",
                    )

    def test_extensions_look_like_extensions(self):
        """Values are file extensions, dot included."""
        for member in SUPPORTED_FORMATS:
            with self.subTest(member=member.name):
                self.assertTrue(member.value.startswith("."))
                self.assertEqual(member.value, member.value.lower())

    def test_geoconcept_gxt_extension(self):
        """Geoconcept Export datasets are .gxt files, not .gml ones."""
        self.assertEqual(FormatsVector.gxt.value, ".gxt")

    def test_supported_formats_contains_every_member(self):
        """SUPPORTED_FORMATS must expose every declared format: it is what the
        CLI builds its default --formats list from, so a format missing here is
        a format `dicogis-cli inventory` never analyzes.
        """
        expected_names = [
            *FormatsVector.__members__,
            *FormatsRaster.__members__,
        ]
        self.assertCountEqual(
            [member.name for member in SUPPORTED_FORMATS], expected_names
        )

    def test_every_supported_format_has_gdal_drivers(self):
        """Each supported format must declare the GDAL/OGR driver(s) able to read
        it, otherwise it can't be gated on driver availability.
        """
        self.assertCountEqual(
            [member.name for member in SUPPORTED_FORMATS],
            FORMAT_TO_GDAL_DRIVERS,
        )
        for drivers in FORMAT_TO_GDAL_DRIVERS.values():
            self.assertIsInstance(drivers, tuple)
            self.assertTrue(len(drivers))


class TestCliDefaultFormats(unittest.TestCase):
    """Test the formats list the CLI analyzes when --formats is not passed."""

    def test_default_formats_lists_every_supported_format(self):
        """`dicogis-cli inventory` derives its per-format opt_analyze_* flags from
        this string, so a format missing from it is silently skipped.
        """
        from dicogis.cli.cmd_inventory import default_formats

        for member in SUPPORTED_FORMATS:
            with self.subTest(format=member.name):
                self.assertIn(member.name, default_formats.split(","))

    def test_gxt_is_analyzed_by_default(self):
        """Regression: `gxt` was absent from the default list, so Geoconcept
        datasets were never inventoried unless --formats named them explicitly.
        """
        from dicogis.cli.cmd_inventory import default_formats

        self.assertIn("gxt", default_formats.split(","))


# ############################################################################
# ####### Stand-alone run ########
# ################################
if __name__ == "__main__":
    unittest.main()
