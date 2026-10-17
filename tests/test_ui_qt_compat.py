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
import os
import subprocess
import sys
from pathlib import Path

# 3rd party
import pytest

# project
from dicogis.ui.qt_compat import QT_API_ENV_VAR, resolve_qt_api


# ##############################################################################
# ########## Globals ###############
# ##################################

# a stand-in for QGIS's qgis.PyQt shim, re-exporting PyQt6 like the real one
# does, plus a marker telling which binding a dicogis module ended up with
_FAKE_QGIS_PYQT = {
    "qgis/__init__.py": "",
    "qgis/PyQt/__init__.py": "",
    "qgis/PyQt/QtCore.py": "from PyQt6.QtCore import *\nFROM_FAKE_QGIS = True\n",
    "qgis/PyQt/QtGui.py": "from PyQt6.QtGui import *\n",
    "qgis/PyQt/QtWidgets.py": "from PyQt6.QtWidgets import *\n",
    "qgis/PyQt/uic.py": "from PyQt6.uic import *\n",
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
    qt_api: str | None, fake_qgis_folder: Path, preload_qgis: bool
) -> subprocess.CompletedProcess:
    """Import the compat layer in a fresh interpreter and report what it picked.

    Args:
        qt_api: value of DICOGIS_QT_API, or None to leave it unset
        fake_qgis_folder: folder holding the fake qgis package, put on PYTHONPATH
        preload_qgis: import qgis before DicoGIS, like a plugin running in QGIS

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
    code = _PROBE.format(preload="import qgis.PyQt\n" if preload_qgis else "")
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


@pytest.mark.parametrize(
    ("requested", "qgis_loaded", "expected"),
    [
        ("auto", False, "pyqt6"),
        ("auto", True, "qgis"),
        ("  AUTO ", False, "pyqt6"),
        ("qgis", False, "qgis"),
        ("pyqt6", True, "pyqt6"),
        ("PyQt6", False, "pyqt6"),
    ],
)
def test_resolve_qt_api(
    monkeypatch: pytest.MonkeyPatch, requested: str, qgis_loaded: bool, expected: str
) -> None:
    if qgis_loaded:
        monkeypatch.setitem(sys.modules, "qgis", object())
    else:
        monkeypatch.delitem(sys.modules, "qgis", raising=False)

    assert resolve_qt_api(requested) == expected


def test_resolve_qt_api_reads_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(QT_API_ENV_VAR, "qgis")
    assert resolve_qt_api() == "qgis"

    monkeypatch.setenv(QT_API_ENV_VAR, "")
    monkeypatch.delitem(sys.modules, "qgis", raising=False)
    assert resolve_qt_api() == "pyqt6"


def test_resolve_qt_api_rejects_unknown_value() -> None:
    with pytest.raises(ValueError, match="DICOGIS_QT_API"):
        resolve_qt_api("pyside6")


@pytest.mark.parametrize(
    ("qt_api", "preload_qgis", "expected"),
    [
        (None, False, "pyqt6 False True True"),
        (None, True, "qgis True True True"),
        ("qgis", False, "qgis True True True"),
        ("pyqt6", True, "pyqt6 False True True"),
    ],
)
def test_submodules_follow_the_selected_binding(
    fake_qgis: Path, qt_api: str | None, preload_qgis: bool, expected: str
) -> None:
    pytest.importorskip("PyQt6.QtWidgets", reason="PyQt6 (gui extra) required")

    result = _probe(qt_api, fake_qgis, preload_qgis)

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == expected


# ##############################################################################
# ##### Stand alone program ########
# ##################################
if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
