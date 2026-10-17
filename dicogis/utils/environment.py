#! python3  # noqa: E265

"""Helpers to retrieve information from execution environment like software versions."""

# ############################################################################
# ########## Libraries #############
# ##################################

# standard library
import logging
import re
import shutil
import subprocess
from os import getenv

# project
from dicogis.constants import FORMAT_TO_GDAL_DRIVERS


# ############################################################################
# ########### Globals ##############
# ##################################

# defined before the optional imports below, which log when they fail
logger = logging.getLogger(__name__)

try:
    from osgeo import gdal, osr

    GDAL_IS_AVAILABLE: bool = True
except ImportError:
    logger.info("GDAL (ou ses bindings Python) n'est pas installé.")
    gdal = osr = None
    GDAL_IS_AVAILABLE: bool = False

try:
    import pyproj

    PYPROJ_IS_AVAILABLE: bool = True
except ImportError:
    logger.info("PyProj n'est pas installé.")
    pyproj = None
    PYPROJ_IS_AVAILABLE: bool = False

# ############################################################################
# ########### Functions ############
# ##################################


def _command_output(*command: str, merge_stderr: bool = False) -> str | None:
    """Run a command-line tool found on the PATH and return its output.

    Args:
        command: executable name, then its arguments
        merge_stderr: also capture what the tool writes to standard error

    Returns:
        output, stripped, or None if the tool is missing or fails
    """
    executable = shutil.which(command[0])
    if executable is None:
        logger.debug(f"{command[0]} not found on the PATH.")
        return None
    try:
        # fixed arguments and an absolute executable path: no untrusted input
        return subprocess.check_output(  # noqa: S603
            [executable, *command[1:]],
            stderr=subprocess.STDOUT if merge_stderr else None,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError) as err:
        logger.debug(f"Running {' '.join(command)} failed. Trace: {err}")
        return None


def get_available_gdal_drivers() -> frozenset[str]:
    """List the short names of every GDAL/OGR driver registered in the
    currently installed GDAL.

    Since GDAL 2.0, raster and vector drivers share a single driver manager,
    so `gdal.GetDriverCount()`/`gdal.GetDriver()` cover both (unlike
    `ogr.GetDriverCount()`, which only reflects a legacy subset).

    Returns:
        short names of the registered drivers, or an empty frozenset if GDAL
        isn't available.
    """
    if not GDAL_IS_AVAILABLE:
        return frozenset()

    gdal.AllRegister()
    return frozenset(gdal.GetDriver(i).ShortName for i in range(gdal.GetDriverCount()))


def is_format_supported_by_gdal(
    format_name: str, available_drivers: frozenset[str] | None = None
) -> bool:
    """Check whether the installed GDAL can actually read a given supported
    format (see `dicogis.constants.FORMAT_TO_GDAL_DRIVERS`).

    Args:
        format_name: a `FormatsVector`/`FormatsRaster` member name (e.g.
            "geojson", "gxt").
        available_drivers: drivers to check against. Defaults to
            `get_available_gdal_drivers()`; pass it explicitly to avoid
            re-enumerating GDAL's driver registry for every format checked.

    Returns:
        True if format_name is unknown (nothing to gate on) or at least one
        of its required drivers is registered, False otherwise.
    """
    if available_drivers is None:
        available_drivers = get_available_gdal_drivers()

    required_drivers = FORMAT_TO_GDAL_DRIVERS.get(format_name)
    if not required_drivers:
        return True

    return any(driver in available_drivers for driver in required_drivers)


def get_gdal_version() -> str:
    """Return GDAL version from gdal-config cmd or from environment variable GDAL_VERSION.

    Returns:
        str: version of GDAL
    """
    gdal_fallback_version = "3.*"

    # if available use,
    if GDAL_IS_AVAILABLE:
        logger.debug(
            f"Version de GDAL obtenue depuis les bindings Python : {gdal.__version__}"
        )
        return gdal.__version__

    # try to get it from gdalinfo (installed with gdal)
    if gdalinfo_output := _command_output("gdalinfo", "--version"):
        logger.debug(f"GDAL version retrieved from gdalinfo: {gdalinfo_output}")
        # e.g. "GDAL 3.10.1, released 2025/01/08"
        if version_match := re.search(r"GDAL (\d+\.\d+\.\d+)", gdalinfo_output):
            return version_match.group(1)

    # try to get it from gdal-config (installed with gdaldev)
    if gdal_config_output := _command_output("gdal-config", "--version"):
        logger.debug(f"GDAL version retrieved from gdal-config: {gdal_config_output}")
        return gdal_config_output

    # first check environment variable
    gdal_version = getenv("GDAL_VERSION")
    if gdal_version:
        return gdal_version

    logger.warning(
        "Unable to retrieve GDAL version from command-line or environment var. "
        f"Using default version: {gdal_fallback_version}"
    )
    return gdal_fallback_version


def get_proj_version() -> str | None:
    """Get PROJ version, using GDAL, PyProj, installed proj binaries or environment
        variable.

    Returns:
        str | None: PROJ's version as Major.Minor.Micro or None if not found
    """
    proj_version = None

    # from GDAL bindings
    if osr is not None and GDAL_IS_AVAILABLE:
        try:
            proj_version = (
                f"{osr.GetPROJVersionMajor()}."
                f"{osr.GetPROJVersionMinor()}."
                f"{osr.GetPROJVersionMicro()}"
            )
            logger.debug(
                f"Version de PROJ obtenue depuis les bindings Python de GDAL : {proj_version}"
            )
            return proj_version
        except Exception as err:
            logger.debug(f"PROJ version not available from GDAL bindings: {err}")

    # from PyProj
    if pyproj is not None and PYPROJ_IS_AVAILABLE:
        try:
            proj_version = pyproj.__proj_version__
            logger.debug(f"Version de PROJ obtenue depuis PyProj : {proj_version}")
            return proj_version
        except Exception as err:
            logger.debug(f"PROJ version not available from PyProj: {err}")

    # from PROJ command-line, which prints its version with its usage message
    if proj_output := _command_output("proj", merge_stderr=True):
        if version_match := re.search(r"Rel\. ([0-9.]+)", proj_output):
            proj_version = version_match.group(1)
            logger.debug(
                f"Version de PROJ obtenue depuis le binaire proj : {proj_version}"
            )
            return proj_version
        logger.error(
            "PROJ est bien installé mais impossible de trouver la version en regex."
        )

    # from environment variable
    if proj_version := getenv("PROJ_VERSION"):
        return proj_version

    logger.warning(
        "Impossible de déterminer la version de PROJ depuis les bindings GDAL, PyProj, "
        "les binaires proj ou la variable d'environnement PROJ_VERSION. "
    )
    return proj_version


# ############################################################################
# ##### Stand alone program ########
# ##################################

if __name__ == "__main__":
    """Standalone execution."""
