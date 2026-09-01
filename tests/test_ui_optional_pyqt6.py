#! python3  # noqa: E265


"""
DicoGIS

Regression test: PyQt6 is an optional dependency (see pyproject.toml `gui`
extra), so `dicogis.ui` and `dicogis.ui.main` (the `dicogis-gui` entry point
module) must stay importable when PyQt6 is not installed — only calling
`dicogis_gui()` itself is expected to fail, with a clear error message.

Run in a subprocess (rather than monkeypatching `sys.modules` in-process):
`dicogis.ui`'s submodules define PyQt6 widget classes at import time, and
forcing them to be re-imported mid-session — as an in-process
`sys.modules` purge would — creates duplicate class objects that confuse
PyQt6/sip and pytest-qt for every other UI test running in the same
session. A subprocess keeps the simulated "PyQt6 missing" state fully
isolated.

Usage from the repo root folder:
    pytest tests/test_ui_optional_pyqt6.py
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# standard library
import subprocess
import sys


# ##############################################################################
# ########## Globals ###############
# ##################################

_SIMULATE_MISSING_PYQT6 = "import sys; sys.modules['PyQt6'] = None; import {module}"

# ##############################################################################
# ########## Functions #############
# ##################################


def _run_import_without_pyqt6(module: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-c", _SIMULATE_MISSING_PYQT6.format(module=module)],
        capture_output=True,
        text=True,
        check=False,
    )


# ##############################################################################
# ########## Tests ##################
# ##################################


def test_dicogis_ui_package_imports_without_pyqt6():
    result = _run_import_without_pyqt6("dicogis.ui")
    assert result.returncode == 0, result.stderr


def test_dicogis_ui_main_imports_without_pyqt6():
    result = _run_import_without_pyqt6("dicogis.ui.main")
    assert result.returncode == 0, result.stderr
