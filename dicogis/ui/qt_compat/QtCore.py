#! python3  # noqa: E265
# ruff: noqa: N999 - module named after the Qt module it mirrors, as qgis.PyQt does

"""`QtCore` from the Qt binding selected by `dicogis.ui.qt_compat`."""

# project
from dicogis.ui.qt_compat import QT_API


if QT_API == "qgis":
    from qgis.PyQt.QtCore import *  # noqa: F403
else:
    from PyQt6.QtCore import *  # noqa: F403
