#! python3  # noqa: E265

"""Qt binding compatibility layer.

DicoGIS's GUI runs either standalone, on PyQt6, or embedded in QGIS (>= 4.4,
Qt >= 6.8), where Qt must be reached through `qgis.PyQt`: QGIS patches some Qt
classes there and its `uic.loadUi` knows about QGIS's own widgets. GUI modules
therefore never import `PyQt6` directly but this package's submodules, which
mirror the `qgis.PyQt` layout:

    from dicogis.ui.qt_compat.QtWidgets import QWidget

The binding is picked once, at first import, from the `DICOGIS_QT_API`
environment variable:

- `auto` (default): `qgis.PyQt` when running inside QGIS, i.e. a
  `QgsApplication` is running, PyQt6 otherwise. QGIS merely being imported is
  not enough: some libraries import `qgis.PyQt` on their own when QGIS is
  installed (pgserviceparser >= 3 does), which loads `qgis.core` in a
  standalone process too.
- `qgis`: always `qgis.PyQt`.
- `pyqt6`: always PyQt6.

Nothing Qt-related is imported here, only in the submodules: PyQt6 is an
optional dependency and importing this package must not require it.
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# standard library
import sys
from os import getenv


# ##############################################################################
# ########## Globals ###############
# ##################################

QT_API_ENV_VAR: str = "DICOGIS_QT_API"
QT_APIS: tuple[str, ...] = ("auto", "qgis", "pyqt6")

# ##############################################################################
# ########## Functions #############
# ##################################


def _qgis_application_is_running() -> bool:
    """Tell whether this process runs inside QGIS (desktop, plugin, qgis_process).

    Never imports QGIS itself: only looks at a `qgis.core` already loaded.

    Returns:
        True if the running Qt application is a QgsApplication
    """
    qgis_core = sys.modules.get("qgis.core")
    qgs_application = getattr(qgis_core, "QgsApplication", None)
    if qgs_application is None:
        return False
    try:
        return isinstance(qgs_application.instance(), qgs_application)
    except Exception:
        return False


def resolve_qt_api(requested: str | None = None) -> str:
    """Determine which Qt binding the GUI must use.

    Args:
        requested: one of `QT_APIS`, case-insensitive. Defaults to the value of
            the `DICOGIS_QT_API` environment variable, or `auto` if unset.

    Raises:
        ValueError: if the requested binding is unknown

    Returns:
        the binding to use: `qgis` or `pyqt6`
    """
    if requested is None:
        requested = getenv(QT_API_ENV_VAR) or "auto"
    requested = requested.strip().lower()

    if requested not in QT_APIS:
        raise ValueError(
            f"Invalid {QT_API_ENV_VAR} value: '{requested}'. "
            f"Expected one of: {', '.join(QT_APIS)}."
        )

    if requested == "auto":
        return "qgis" if _qgis_application_is_running() else "pyqt6"
    return requested


QT_API: str = resolve_qt_api()
