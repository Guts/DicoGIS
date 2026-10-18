#! python3  # noqa: E265


"""
Guards the rule that GUI widgets are declared in Qt Designer .ui files.

Fails on any Qt widget or layout, or any of the project's own widgets
(dicogis/ui/wdg_*.py), instantiated by a module of dicogis/ui (see
"Graphical interface" in CONTRIBUTING.md): it belongs in the module's .ui file,
the project's own widgets included, placed there by promotion. Dialogs opened at
runtime (QDialog subclasses, e.g. QMessageBox) and the stand-alone test blocks
(`if __name__ == "__main__":`) are allowed.

Usage from the repo root folder:
    pytest tests/test_ui_widgets_in_ui_files.py
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# standard library
import ast
import sys
from pathlib import Path

# 3rd party
import pytest

# project
from dicogis.ui.qt_compat import QtWidgets


# ##############################################################################
# ########## Globals ###############
# ##################################

UI_FOLDER = Path(__file__).parent.parent / "dicogis" / "ui"
QT_WIDGETS_MODULE = "dicogis.ui.qt_compat.QtWidgets"
# modules of the project's own widgets, placed in .ui files by promotion
PROJECT_WIDGETS_MODULES = "dicogis.ui.wdg_"

# ##############################################################################
# ########## Functions #############
# ##################################


def _is_forbidden(module: str, class_name: str) -> bool:
    """Tell whether instantiating a class builds the interface in Python.

    Args:
        module: module the class is imported from
        class_name: name of the class

    Returns:
        True for the project's widgets and Qt widgets and layouts, False for
        dialogs and anything else
    """
    if module.startswith(PROJECT_WIDGETS_MODULES):
        return True
    if module != QT_WIDGETS_MODULE:
        return False
    qt_class = getattr(QtWidgets, class_name, None)
    if not isinstance(qt_class, type):
        return False
    if issubclass(qt_class, QtWidgets.QDialog):
        return False
    return issubclass(qt_class, (QtWidgets.QWidget, QtWidgets.QLayout))


def _is_main_block(node: ast.AST) -> bool:
    """Tell whether a node is the `if __name__ == "__main__":` test block."""
    return (
        isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and isinstance(node.test.left, ast.Name)
        and node.test.left.id == "__name__"
    )


def _widget_instantiations(py_path: Path) -> list[str]:
    """List the widgets and layouts a module instantiates.

    Args:
        py_path: path to a Python module

    Returns:
        "<file>:<line> <class>" for each instantiation outside the test block
    """
    tree = ast.parse(py_path.read_text(encoding="UTF-8"))
    imported = {
        alias.asname or alias.name: (node.module, alias.name)
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
        for alias in node.names
    }

    found: list[str] = []
    module_code = [n for n in tree.body if not _is_main_block(n)]
    for node in (child for top in module_code for child in ast.walk(top)):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in imported
            and _is_forbidden(*imported[node.func.id])
        ):
            relative_path = py_path.relative_to(UI_FOLDER)
            found.append(f"{relative_path}:{node.lineno} {node.func.id}")
    return found


# ##############################################################################
# ########## Tests ##################
# ##################################


def test_widget_detection() -> None:
    """Guard the guard: detection must catch widgets and layouts, not dialogs."""
    assert _is_forbidden(QT_WIDGETS_MODULE, "QCheckBox")
    assert _is_forbidden(QT_WIDGETS_MODULE, "QVBoxLayout")
    assert _is_forbidden("dicogis.ui.wdg_scrollable_table", "ScrollableTable")
    assert not _is_forbidden(QT_WIDGETS_MODULE, "QMessageBox")
    assert not _is_forbidden(QT_WIDGETS_MODULE, "QTableWidgetItem")
    assert not _is_forbidden(QT_WIDGETS_MODULE, "QApplication")
    assert not _is_forbidden(
        "dicogis.ui.dialogs.dlg_database_connection", "DatabaseConnectionDialog"
    )


@pytest.mark.parametrize(
    "py_path",
    sorted(
        p
        for p in UI_FOLDER.rglob("*.py")
        if "qt_compat" not in p.relative_to(UI_FOLDER).parts
    ),
    ids=lambda p: str(p.relative_to(UI_FOLDER)),
)
def test_no_widget_built_in_python(py_path: Path) -> None:
    found = _widget_instantiations(py_path)

    assert not found, (
        f"Widgets built in Python: {found}. Declare them in the matching .ui "
        "file instead (promote the project's own widgets)."
    )


# ##############################################################################
# ##### Stand alone program ########
# ##################################
if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
