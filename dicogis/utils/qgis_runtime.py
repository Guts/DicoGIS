#! python3  # noqa: E265

"""Detection of a running QGIS, shared by the Qt binding and the network layers.

Kept apart from dicogis.utils.environment, which imports GDAL and PyProj: the Qt
binding is resolved at first import and must not load them.
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# standard library
import sys


# ##############################################################################
# ########## Functions #############
# ##################################


def qgis_application_is_running() -> bool:
    """Tell whether this process runs inside QGIS (desktop, plugin, qgis_process).

    Never imports QGIS itself: only looks at a `qgis.core` already loaded. QGIS merely
    being imported is not enough: some libraries import it on their own when QGIS is
    installed (pgserviceparser >= 3 does), which loads `qgis.core` in a standalone
    process too.

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
