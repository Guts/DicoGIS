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

# 3rd party
from packaging.version import parse

# project
from dicogis.utils.environment import get_gdal_version, get_proj_version

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


# ############################################################################
# ####### Stand-alone run ########
# ################################
if __name__ == "__main__":
    unittest.main()
