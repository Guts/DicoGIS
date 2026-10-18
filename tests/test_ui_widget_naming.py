#! python3  # noqa: E265


"""
Guards the widget naming convention of the Qt Designer files.

Every widget declared in a .ui file must be named after its class prefix
(see "Graphical interface" in CONTRIBUTING.md), since its objectName becomes
the Python attribute holding it. Reads the .ui files as XML: needs neither
PyQt6 nor GDAL.

Usage from the repo root folder:
    pytest tests/test_ui_widget_naming.py
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# standard library
import re
import sys
from pathlib import Path
from xml.etree import ElementTree

# 3rd party
import pytest


# ##############################################################################
# ########## Globals ###############
# ##################################

UI_FOLDER = Path(__file__).parent.parent / "dicogis" / "ui"

# keep in sync with the table in CONTRIBUTING.md
WIDGET_PREFIXES: dict[str, str] = {
    "QCheckBox": "cbx_",
    "QComboBox": "cbb_",
    "QDialog": "dlg_",
    "QDialogButtonBox": "bbx_",
    "QFrame": "frm_",
    "QGroupBox": "grp_",
    "QLabel": "lbl_",
    "QLineEdit": "lne_",
    "QListWidget": "lst_",
    "QMainWindow": "mw_",
    "QProgressBar": "prg_",
    "QPushButton": "btn_",
    "QRadioButton": "rbn_",
    "QSpinBox": "sbx_",
    "QTabWidget": "tab_",
    "QTableView": "tbv_",
    "QTableWidget": "tbw_",
    "QTextEdit": "txt_",
    "QToolButton": "btn_",
    "QWidget": "wdg_",
    "QgsCollapsibleGroupBox": "qgrp_",
    "QgsFileWidget": "qfil_",
    "QgsSpinBox": "qsbx_",
}

# the project's own widgets (tab pages, tables…), promoted in Qt Designer
CUSTOM_WIDGET_PREFIX = "wdg_"

# PEP 8 attribute name: lowercase words separated by underscores
SNAKE_CASE = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)+$")

# ##############################################################################
# ########## Functions #############
# ##################################


def _ui_roots() -> list[tuple[str, ElementTree.Element]]:
    """Parse every GUI .ui file.

    Returns:
        (.ui file relative path, XML root element) tuples
    """
    roots: list[tuple[str, ElementTree.Element]] = []
    for ui_path in sorted(UI_FOLDER.rglob("*.ui")):
        # noqa S314: the parsed files are the project's own interface sources
        root = ElementTree.parse(ui_path).getroot()  # noqa: S314
        roots.append((str(ui_path.relative_to(UI_FOLDER)), root))
    return roots


def _declared_widgets() -> list[tuple[str, str, str]]:
    """List every widget declared in the GUI .ui files.

    Returns:
        (.ui file relative path, widget class, objectName) tuples
    """
    return [
        (ui_file, w.get("class"), w.get("name"))
        for ui_file, root in _ui_roots()
        for w in root.iter("widget")
    ]


def _widget_prefixes() -> dict[str, str]:
    """Map widget classes to their prefix, custom widgets included.

    The project's own widgets, placed in a .ui file by promotion (declared in its
    <customwidgets> section), take the generic custom widget prefix.

    Returns:
        widget class -> prefix
    """
    custom_classes = {
        custom.findtext("class")
        for _, root in _ui_roots()
        for custom in root.iter("customwidget")
    }
    return WIDGET_PREFIXES | dict.fromkeys(custom_classes, CUSTOM_WIDGET_PREFIX)


# ##############################################################################
# ########## Tests ##################
# ##################################


def test_ui_files_are_found() -> None:
    """Guard the guard: finding no widget would make the tests below pass."""
    assert len(_declared_widgets()) > 50


def test_every_widget_class_has_a_prefix() -> None:
    unknown = sorted(
        {cls for _, cls, _ in _declared_widgets()} - _widget_prefixes().keys()
    )

    assert not unknown, (
        f"No naming prefix defined for {unknown}: add one to WIDGET_PREFIXES "
        "and to the table in CONTRIBUTING.md."
    )


@pytest.mark.parametrize(
    ("ui_file", "widget_class", "name"),
    [w for w in _declared_widgets() if w[1] in _widget_prefixes()],
    ids=lambda value: str(value),
)
def test_widget_is_named_after_its_class(
    ui_file: str, widget_class: str, name: str
) -> None:
    prefix = _widget_prefixes()[widget_class]

    assert name.startswith(prefix) and SNAKE_CASE.match(name), (
        f"{ui_file}: {widget_class} '{name}' should be snake_case and start "
        f"with '{prefix}'"
    )


# ##############################################################################
# ##### Stand alone program ########
# ##################################
if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
