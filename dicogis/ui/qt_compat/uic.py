#! python3  # noqa: E265

"""`uic` from the Qt binding selected by `dicogis.ui.qt_compat`."""

# project
from dicogis.ui.qt_compat import QT_API


if QT_API == "qgis":
    from qgis.PyQt.uic import *  # noqa: F403
else:
    from PyQt6.uic import *  # noqa: F403
