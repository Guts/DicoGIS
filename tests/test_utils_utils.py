#! python3  # noqa E265

"""
Usage from the repo root folder:

.. code-block:: bash
    # for whole tests
    python -m unittest tests.test_utils_utils
    # for specific test
    python -m unittest tests.test_utils_utils.TestResolveInternalPath.test_normal_python_mode
"""

# standard library
import sys
import unittest
from importlib import resources
from pathlib import Path
from unittest.mock import patch

# project
from dicogis.__about__ import __package_name__
from dicogis.utils.utils import Utilities

# ############################################################################
# ########## Classes #############
# ################################


class TestResolveInternalPath(unittest.TestCase):
    """Test Utilities.resolve_internal_path()."""

    def test_normal_python_mode_resolves_relative_to_package(self):
        result = Utilities.resolve_internal_path(internal_path=Path("locale"))

        expected = Path(resources.files(__package_name__)).joinpath(Path("locale"))
        self.assertEqual(result, expected)

    def test_frozen_mode_with_meipass_resolves_relative_to_meipass(self):
        with (
            patch.object(sys, "frozen", True, create=True),
            patch.object(sys, "_MEIPASS", "/fake/frozen/root", create=True),
        ):
            result = Utilities.resolve_internal_path(internal_path=Path("locale"))

        self.assertEqual(result, Path("/fake/frozen/root/locale"))

    def test_frozen_flag_without_meipass_falls_back_to_normal_mode(self):
        """sys.frozen alone (without _MEIPASS) does not trigger frozen-mode
        resolution -- both conditions are required."""
        with patch.object(sys, "frozen", True, create=True):
            self.assertFalse(hasattr(sys, "_MEIPASS"))
            result = Utilities.resolve_internal_path(internal_path=Path("locale"))

        expected = Path(resources.files(__package_name__)).joinpath(Path("locale"))
        self.assertEqual(result, expected)


# ############################################################################
# ####### Stand-alone run ########
# ################################
if __name__ == "__main__":
    unittest.main()
