#! python3  # noqa: E265


"""
Tests for the Qt binding compatibility layer (dicogis.ui.qt_compat).

The binding is resolved once, at import time, and the qgis.PyQt branch needs a
QGIS install: both are exercised in subprocesses, with a fake `qgis.PyQt`
package standing in for QGIS, so the selection logic is tested without QGIS and
without leaking module state into the other UI tests.

Usage from the repo root folder:
    pytest tests/test_ui_qt_compat.py
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# standard library
import ast
import os
import subprocess
import sys
import types
from pathlib import Path

# 3rd party
import pytest

# project
from dicogis.ui.qt_compat import QT_API_ENV_VAR, resolve_qt_api


# ##############################################################################
# ########## Globals ###############
# ##################################

UI_FOLDER = Path(__file__).parent.parent / "dicogis" / "ui"
# the only GUI modules allowed to name a binding: the compat layer itself
QT_COMPAT_FOLDER = UI_FOLDER / "qt_compat"
QT_BINDINGS = ("PyQt6", "PyQt5", "PySide6", "qgis")

# a stand-in for QGIS's qgis.PyQt shim, re-exporting PyQt6 like the real one
# does, plus a marker telling which binding a dicogis module ended up with, and
# a qgis.core whose QgsApplication is running only once a test says so
_FAKE_QGIS_PYQT = {
    "qgis/__init__.py": "",
    "qgis/core.py": (
        "class QgsApplication:\n"
        "    running = None\n"
        "    @classmethod\n"
        "    def instance(cls):\n"
        "        return cls.running\n"
    ),
    "qgis/PyQt/__init__.py": "",
    "qgis/PyQt/QtCore.py": "from PyQt6.QtCore import *\nFROM_FAKE_QGIS = True\n",
    "qgis/PyQt/QtGui.py": "from PyQt6.QtGui import *\n",
    "qgis/PyQt/QtWidgets.py": "from PyQt6.QtWidgets import *\n",
    "qgis/PyQt/uic.py": "from PyQt6.uic import *\n",
}

# what each scenario runs before importing DicoGIS
_PRELOADS = {
    "standalone": "",
    # what pgserviceparser >= 3 does on import when QGIS is installed
    "qgis_imported": "import qgis.PyQt\nimport qgis.core\n",
    "qgis_running": (
        "import qgis.core\n"
        "qgis.core.QgsApplication.running = qgis.core.QgsApplication()\n"
    ),
}

_PROBE = (
    "import sys\n"
    "{preload}"
    "from dicogis.ui.qt_compat import QT_API\n"
    "from dicogis.ui.qt_compat import QtCore, QtWidgets, uic\n"
    "print(QT_API, getattr(QtCore, 'FROM_FAKE_QGIS', False),"
    " hasattr(QtWidgets, 'QWidget'), hasattr(uic, 'loadUi'))\n"
)

# ##############################################################################
# ########## Fixtures ##############
# ##################################


@pytest.fixture
def fake_qgis(tmp_path: Path) -> Path:
    """Write a fake qgis.PyQt package and return the folder holding it."""
    for relative_path, content in _FAKE_QGIS_PYQT.items():
        module_path = tmp_path / relative_path
        module_path.parent.mkdir(parents=True, exist_ok=True)
        module_path.write_text(content, encoding="UTF-8")
    return tmp_path


# ##############################################################################
# ########## Functions #############
# ##################################


def _probe(
    qt_api: str | None, fake_qgis_folder: Path, scenario: str
) -> subprocess.CompletedProcess:
    """Import the compat layer in a fresh interpreter and report what it picked.

    Args:
        qt_api: value of DICOGIS_QT_API, or None to leave it unset
        fake_qgis_folder: folder holding the fake qgis package, put on PYTHONPATH
        scenario: key of _PRELOADS, the QGIS state before DicoGIS is imported

    Returns:
        the finished subprocess, its stdout being "<QT_API> <from fake qgis>
        <has QWidget> <has loadUi>"
    """
    env = {k: v for k, v in os.environ.items() if k != QT_API_ENV_VAR}
    if qt_api is not None:
        env[QT_API_ENV_VAR] = qt_api
    env["PYTHONPATH"] = os.pathsep.join(
        [str(fake_qgis_folder), str(Path(__file__).parent.parent)]
    )
    code = _PROBE.format(preload=_PRELOADS[scenario])
    # the command is this interpreter running a constant snippet: no untrusted input
    return subprocess.run(  # noqa: S603
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


# ##############################################################################
# ########## Tests ##################
# ##################################


def _set_qgis_state(monkeypatch: pytest.MonkeyPatch, qgis_state: str) -> None:
    """Fake the QGIS state of the process, in sys.modules.

    Args:
        monkeypatch: pytest fixture
        qgis_state: "absent", "imported" (qgis.core loaded, no QgsApplication,
            as pgserviceparser >= 3 causes), "other_app" (a plain Qt application
            runs) or "running" (inside QGIS)
    """
    if qgis_state == "absent":
        monkeypatch.delitem(sys.modules, "qgis.core", raising=False)
        return

    class QgsApplication:
        running = None

        @classmethod
        def instance(cls) -> object:
            return cls.running

    if qgis_state == "running":
        QgsApplication.running = QgsApplication()
    elif qgis_state == "other_app":
        QgsApplication.running = object()
    qgis_core = types.ModuleType("qgis.core")
    qgis_core.QgsApplication = QgsApplication
    monkeypatch.setitem(sys.modules, "qgis.core", qgis_core)


@pytest.mark.parametrize(
    ("requested", "qgis_state", "expected"),
    [
        ("auto", "absent", "pyqt6"),
        ("auto", "imported", "pyqt6"),
        ("auto", "other_app", "pyqt6"),
        ("auto", "running", "qgis"),
        ("  AUTO ", "absent", "pyqt6"),
        ("qgis", "absent", "qgis"),
        ("pyqt6", "running", "pyqt6"),
        ("PyQt6", "absent", "pyqt6"),
    ],
)
def test_resolve_qt_api(
    monkeypatch: pytest.MonkeyPatch, requested: str, qgis_state: str, expected: str
) -> None:
    _set_qgis_state(monkeypatch, qgis_state)

    assert resolve_qt_api(requested) == expected


def test_resolve_qt_api_survives_a_failing_qgis_check(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    qgis_core = types.ModuleType("qgis.core")
    qgis_core.QgsApplication = type(
        "QgsApplication", (), {"instance": staticmethod(lambda: 1 / 0)}
    )
    monkeypatch.setitem(sys.modules, "qgis.core", qgis_core)

    assert resolve_qt_api("auto") == "pyqt6"


def test_resolve_qt_api_reads_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(QT_API_ENV_VAR, "qgis")
    assert resolve_qt_api() == "qgis"

    monkeypatch.setenv(QT_API_ENV_VAR, "")
    _set_qgis_state(monkeypatch, "absent")
    assert resolve_qt_api() == "pyqt6"


def test_resolve_qt_api_rejects_unknown_value() -> None:
    with pytest.raises(ValueError, match="DICOGIS_QT_API"):
        resolve_qt_api("pyside6")


@pytest.mark.parametrize(
    ("qt_api", "scenario", "expected"),
    [
        (None, "standalone", "pyqt6 False True True"),
        # QGIS installed and imported by a library, but not running: standalone
        (None, "qgis_imported", "pyqt6 False True True"),
        (None, "qgis_running", "qgis True True True"),
        ("qgis", "standalone", "qgis True True True"),
        ("pyqt6", "qgis_running", "pyqt6 False True True"),
    ],
)
def test_submodules_follow_the_selected_binding(
    fake_qgis: Path, qt_api: str | None, scenario: str, expected: str
) -> None:
    pytest.importorskip("PyQt6.QtWidgets", reason="PyQt6 (gui extra) required")

    result = _probe(qt_api, fake_qgis, scenario)

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == expected


def test_gui_modules_import_qt_only_through_the_compat_layer() -> None:
    """A direct `PyQt6` import would bypass the binding selected for QGIS."""
    offenders: list[str] = []
    for module_path in sorted(UI_FOLDER.rglob("*.py")):
        if QT_COMPAT_FOLDER in module_path.parents:
            continue
        tree = ast.parse(module_path.read_text(encoding="UTF-8"), str(module_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            else:
                continue
            offenders.extend(
                f"{module_path.relative_to(UI_FOLDER)}:{node.lineno} {name}"
                for name in names
                if name.split(".")[0] in QT_BINDINGS
            )

    assert not offenders, (
        f"Import Qt from dicogis.ui.qt_compat instead of a binding: {offenders}"
    )


# ##############################################################################
# ##### Stand alone program ########
# ##################################
if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
