#! python3  # noqa E265

"""
Usage from the repo root folder:
    python -m unittest tests.test_models_data_format
"""

# standard library
import unittest

# project
from dicogis.models.data_format import FormatMatcher


# ############################################################################
# ########## Classes #############
# ################################


class TestFormatMatcher(unittest.TestCase):
    """Test the FormatMatcher dataclass.

    Note: FormatMatcher isn't referenced anywhere else in the codebase
    (dicogis/, tests/) -- this is a minimal construction/field-storage
    smoke test rather than behavioral coverage, since there's no behavior
    to exercise beyond the dataclass's generated __init__.
    """

    def test_stores_every_field_as_given(self):
        format_matcher = FormatMatcher(
            name="ESRI File Geodatabase",
            alternative_names=["esri_filegdb", "filegdb"],
            data_structure="directory",
            gdal_long_name="ESRI File Geodatabase",
            gdal_short_name="OpenFileGDB",
            extension=".gdb",
            dependencies_required=[],
            dependencies_optional=[],
            storage_kind="directory",
        )

        self.assertEqual(format_matcher.name, "ESRI File Geodatabase")
        self.assertEqual(format_matcher.alternative_names, ["esri_filegdb", "filegdb"])
        self.assertEqual(format_matcher.extension, ".gdb")


# ############################################################################
# ####### Stand-alone run ########
# ################################
if __name__ == "__main__":
    unittest.main()
