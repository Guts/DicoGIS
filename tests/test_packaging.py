#! python3  # noqa E265

"""
Usage from the repo root folder:

.. code-block:: bash
    # for whole tests
    python -m unittest tests.test_packaging
    # for specific test
    python -m unittest tests.test_packaging.TestPackaging.test_ui_and_translation_files_are_packaged
"""

# standard library
import tomllib
import unittest
from pathlib import Path

# 3rd party
from packaging.requirements import Requirement


# ############################################################################
# ########## Globals #############
# ################################

PROJECT_ROOT = Path(__file__).parent.parent
PACKAGE_DIR = PROJECT_ROOT / "dicogis"

# Qt files loaded at runtime: if one is missing from the wheel, the GUI breaks
RUNTIME_DATA_SUFFIXES = {".ui", ".qm"}


# ############################################################################
# ########## Classes #############
# ################################


class TestPackaging(unittest.TestCase):
    """Test the packaging configuration declared in pyproject.toml."""

    @classmethod
    def setUpClass(cls) -> None:
        """Read pyproject.toml once."""
        with (PROJECT_ROOT / "pyproject.toml").open("rb") as pyproject_file:
            cls.pyproject = tomllib.load(pyproject_file)

        cls.package_data_patterns: list[str] = cls.pyproject["tool"]["setuptools"][
            "package-data"
        ]["dicogis"]

    def test_package_data_patterns_match_files(self) -> None:
        """A pattern matching nothing is a typo or a moved folder: files would be
        silently left out of the wheel.
        """
        for pattern in self.package_data_patterns:
            with self.subTest(pattern=pattern):
                self.assertTrue(any(PACKAGE_DIR.glob(pattern)))

    def test_ui_and_translation_files_are_packaged(self) -> None:
        """Every .ui and .qm file must be covered by a package-data pattern, e.g. a
        new dialog in a new subfolder.
        """
        packaged = {
            path
            for pattern in self.package_data_patterns
            for path in PACKAGE_DIR.glob(pattern)
        }
        runtime_data = {
            path
            for path in PACKAGE_DIR.rglob("*")
            if path.suffix in RUNTIME_DATA_SUFFIXES
        }

        missing = sorted(
            str(path.relative_to(PROJECT_ROOT)) for path in runtime_data - packaged
        )
        self.assertEqual(missing, [], "Not declared in [tool.setuptools.package-data]")

    def test_build_requires_setuptools_supports_spdx_license(self) -> None:
        """An SPDX `license` expression (PEP 639) is only understood by setuptools
        >= 77: with a lower floor, builds without isolation fail.
        """
        if not isinstance(self.pyproject["project"]["license"], str):
            self.skipTest("The license is not declared as an SPDX expression.")

        requirements = [
            Requirement(requirement)
            for requirement in self.pyproject["build-system"]["requires"]
        ]
        setuptools = next(req for req in requirements if req.name == "setuptools")

        self.assertNotIn("76.1.0", setuptools.specifier)
        self.assertIn("77.0.0", setuptools.specifier)


# ############################################################################
# ####### Stand-alone run ########
# ################################
if __name__ == "__main__":
    unittest.main()
