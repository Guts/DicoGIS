#! python3  # noqa E265

"""
Usage from the repo root folder:

.. code-block:: bash
    # for whole tests
    python -m unittest tests.test_about
    # for specific test
    python -m unittest tests.test_about.TestAbout.test_version_semver
"""

# standard library
import unittest
from importlib.metadata import PackageNotFoundError, version as installed_version

# 3rd party
from packaging.version import Version, parse
from validators import url

# project
from dicogis import __about__


# ############################################################################
# ########## Classes #############
# ################################


class TestAbout(unittest.TestCase):
    """Test package metadata."""

    def test_metadata_types(self):
        """Test types."""
        # general
        self.assertIsInstance(__about__.__author__, str)
        self.assertIsInstance(__about__.__copyright__, str)
        self.assertIsInstance(__about__.__email__, str)
        self.assertIsInstance(__about__.__executable_name__, str)
        self.assertIsInstance(__about__.__package_name__, str)
        self.assertIsInstance(__about__.__keywords__, list)
        self.assertIsInstance(__about__.__license__, str)
        self.assertIsInstance(__about__.__summary__, str)
        self.assertIsInstance(__about__.__title__, str)
        self.assertIsInstance(__about__.__title_clean__, str)
        self.assertIsInstance(__about__.__uri_homepage__, str)
        self.assertIsInstance(__about__.__uri_repository__, str)
        self.assertIsInstance(__about__.__uri_tracker__, str)
        self.assertIsInstance(__about__.__uri__, str)
        self.assertIsInstance(__about__.__version__, str)
        self.assertIsInstance(__about__.__version_info__, tuple)

        # misc
        self.assertLessEqual(len(__about__.__title_clean__), len(__about__.__title__))

        # urls
        self.assertTrue(url(__about__.__uri_homepage__))
        self.assertTrue(url(__about__.__uri_repository__))
        self.assertTrue(url(__about__.__uri_tracker__))
        self.assertTrue(url(__about__.__uri__))

    def test_version_semver(self):
        """Test if version comply with semantic versioning."""
        self.assertTrue(parse(__about__.__version__))

    def test_version_matches_distribution_metadata(self):
        """The built distribution must report the version single-sourced from
        __about__, not a stale copy: pyproject.toml declares it as dynamic, so a
        static `version` re-added to [project] would silently shadow it and ship
        packages labelled with the wrong version.
        """
        try:
            dist_version = installed_version(__about__.__package_name__)
        except PackageNotFoundError:
            self.skipTest("dicogis is not installed: no distribution metadata to check")

        # compared as PEP 440 versions: metadata stores the normalized form
        # ("4.0.0b12") of what __about__ spells "4.0.0-beta12"
        self.assertEqual(Version(dist_version), Version(__about__.__version__))


# ############################################################################
# ####### Stand-alone run ########
# ################################
if __name__ == "__main__":
    unittest.main()
