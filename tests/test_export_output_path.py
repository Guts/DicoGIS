#! python3  # noqa E265

"""
Usage from the repo root folder:

.. code-block:: bash
    # for whole tests
    python -m unittest tests.test_export_output_path
    # for specific test
    python -m unittest tests.test_export_output_path.TestDetermineOutputPath.test_explicit_output_path_wins_over_everything_else
"""

# standard library
import unittest
from datetime import date
from pathlib import Path

# project
from dicogis.export.output_path import determine_output_path


# ############################################################################
# ########## Classes #############
# ################################


class TestDetermineOutputPath(unittest.TestCase):
    """Test determine_output_path()."""

    def test_explicit_output_path_wins_over_everything_else(self):
        result = determine_output_path(
            output_path=Path("explicit.xlsx"),
            output_format="excel",
            input_folder=Path("some/folder"),
        )

        self.assertEqual(result, Path("explicit.xlsx"))

    def test_excel_default_name_from_input_folder(self):
        result = determine_output_path(
            output_path=None,
            output_format="excel",
            input_folder=Path("some/folder"),
        )

        self.assertEqual(result, Path(f"DicoGIS_folder_{date.today()}.xlsx"))

    def test_excel_default_name_from_pg_services(self):
        result = determine_output_path(
            output_path=None,
            output_format="excel",
            pg_services=["srv_a", "srv_b"],
        )

        self.assertEqual(
            result, Path(f"DicoGIS_PostGIS_srv_a__srv_b_{date.today()}.xlsx")
        )

    def test_json_default_name_is_a_folder_without_extension(self):
        result = determine_output_path(
            output_path=None,
            output_format="json",
            input_folder=Path("some/folder"),
        )

        self.assertEqual(result, Path(f"DicoGIS_folder_{date.today()}"))

    def test_udata_default_name_is_a_folder_without_extension(self):
        result = determine_output_path(
            output_path=None,
            output_format="udata",
            input_folder=Path("some/folder"),
        )

        self.assertEqual(result, Path(f"DicoGIS_folder_{date.today()}"))

    def test_json_default_name_from_pg_services(self):
        result = determine_output_path(
            output_path=None,
            output_format="json",
            pg_services=["srv_a"],
        )

        self.assertEqual(result, Path(f"DicoGIS_srv_a_{date.today()}"))

    def test_unsupported_format_without_explicit_path_raises_valueerror(self):
        with self.assertRaises(ValueError):
            determine_output_path(
                output_path=None,
                output_format="bogus",
                input_folder=Path("some/folder"),
            )

    def test_known_gap_no_folder_and_no_pg_services_returns_none(self):
        """Document a gap: with no output_path, no input_folder and no
        pg_services, the function falls through every branch and returns
        None instead of a Path or raising. inventory() never hits this in
        practice because it validates that at least one of input_folder/
        pg_services is set before calling determine_output_path()."""
        result = determine_output_path(
            output_path=None,
            output_format="excel",
            input_folder=None,
            pg_services=None,
        )

        self.assertIsNone(result)


# ############################################################################
# ####### Stand-alone run ########
# ################################
if __name__ == "__main__":
    unittest.main()
