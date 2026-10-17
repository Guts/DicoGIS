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

# PEP 8 attribute name: lowercase words separated by underscores
SNAKE_CASE = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)+$")

# ##############################################################################
# ########## Functions #############
# ##################################


def _declared_widgets() -> list[tuple[str, str, str]]:
    """List every widget declared in the GUI .ui files.

    Returns:
        (.ui file relative path, widget class, objectName) tuples
    """
    widgets: list[tuple[str, str, str]] = []
    for ui_path in sorted(UI_FOLDER.rglob("*.ui")):
        # noqa S314: the parsed files are the project's own interface sources
        root = ElementTree.parse(ui_path).getroot()  # noqa: S314
        widgets.extend(
            (str(ui_path.relative_to(UI_FOLDER)), w.get("class"), w.get("name"))
            for w in root.iter("widget")
        )
    return widgets


# ##############################################################################
# ########## Tests ##################
# ##################################


def test_ui_files_are_found() -> None:
    """Guard the guard: finding no widget would make the tests below pass."""
    assert len(_declared_widgets()) > 50


def test_every_widget_class_has_a_prefix() -> None:
    unknown = sorted(
        {cls for _, cls, _ in _declared_widgets()} - WIDGET_PREFIXES.keys()
    )

    assert not unknown, (
        f"No naming prefix defined for {unknown}: add one to WIDGET_PREFIXES "
        "and to the table in CONTRIBUTING.md."
    )


@pytest.mark.parametrize(
    ("ui_file", "widget_class", "name"),
    [w for w in _declared_widgets() if w[1] in WIDGET_PREFIXES],
    ids=lambda value: str(value),
)
def test_widget_is_named_after_its_class(
    ui_file: str, widget_class: str, name: str
) -> None:
    prefix = WIDGET_PREFIXES[widget_class]

    assert name.startswith(prefix) and SNAKE_CASE.match(name), (
        f"{ui_file}: {widget_class} '{name}' should be snake_case and start "
        f"with '{prefix}'"
    )


# ##############################################################################
# ##### Stand alone program ########
# ##################################
if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
