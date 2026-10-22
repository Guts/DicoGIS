#! python3  # noqa: E265


"""
Guards the frozen GUI builds against widgets only imported through .ui files.

Promoted widgets are named in the `<customwidgets>` headers of .ui files and imported
at runtime by `uic.loadUi()`: PyInstaller's static analysis can't see them, so the
GUI builder scripts must collect the `dicogis.ui` submodules explicitly (see #522).

Usage from the repo root folder:
    pytest tests/test_builder_ui_modules.py
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# standard library
import importlib.util
import xml.etree.ElementTree as ET
from pathlib import Path

# 3rd party
import pytest


# ##############################################################################
# ########## Globals ###############
# ##################################

REPO_FOLDER = Path(__file__).parent.parent
UI_FILES = sorted((REPO_FOLDER / "dicogis" / "ui").rglob("*.ui"))
GUI_BUILDERS = sorted((REPO_FOLDER / "builder").glob("pyinstaller_build_*_gui.py"))

# ##############################################################################
# ########## Functions #############
# ##################################


def _promoted_modules(ui_file: Path) -> list[str]:
    """List the Python modules named by the custom widgets of a .ui file."""
    root = ET.parse(ui_file).getroot()  # noqa: S314 (repo files, trusted)
    return [h.text.strip() for h in root.iterfind(".//customwidget/header") if h.text]


# ##############################################################################
# ########## Tests #################
# ##################################


@pytest.mark.parametrize("ui_file", UI_FILES, ids=lambda p: p.name)
def test_promoted_widgets_modules_exist(ui_file: Path) -> None:
    """Every module named in a .ui custom widget header must exist in the package."""
    for module in _promoted_modules(ui_file):
        assert importlib.util.find_spec(module) is not None, (
            f"{ui_file.name}: no module {module}"
        )


def test_gui_builders_found() -> None:
    """Avoid a silent pass of the next test if the builders get renamed."""
    assert GUI_BUILDERS


@pytest.mark.parametrize("builder", GUI_BUILDERS, ids=lambda p: p.name)
def test_gui_builders_collect_ui_submodules(builder: Path) -> None:
    """GUI builders must bundle the modules that .ui files import dynamically."""
    assert "--collect-submodules=dicogis.ui" in builder.read_text(encoding="utf-8")
