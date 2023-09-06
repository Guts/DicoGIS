#! python3  # noqa: E265

"""Helpers to retrieve information from execution environment like software versions."""

# ############################################################################
# ########## Libraries #############
# ##################################

# standard library
import logging
import re
import subprocess
from os import getenv

try:
    from osgeo import gdal, osr

    GDAL_IS_AVAILABLE: bool = True
except ImportError:
    logging.info("GDAL (ou ses bindings Python) n'est pas installé.")
    gdal = osr = None
    GDAL_IS_AVAILABLE: bool = False

try:
    import pyproj

    PYPROJ_IS_AVAILABLE: bool = True
except ImportError:
    logging.info("PyProj n'est pas installé.")
    pyproj = None
    PYPROJ_IS_AVAILABLE: bool = False

# ############################################################################
# ########### Globals ##############
# ##################################

# logs
logger = logging.getLogger(__name__)

# ############################################################################
# ########### Functions ############
# ##################################


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
    try:
        returned_output: bytes = subprocess.check_output(
            "gdalinfo --version", shell=True
        )
        logger.debug(
            f"GDAL version retrieved from gdalinfo: {returned_output.decode('utf-8')}"
        )
        return returned_output[5:10].decode("utf-8")
    except Exception:
        pass

    # try to get it from gdal-config (installed with gdaldev)
    try:
        returned_output: bytes = subprocess.check_output(
            "gdal-config --version", shell=True
        )
        logger.debug(
            f"GDAL version retrieved from gdal-config: {returned_output.decode('utf-8')}"
        )
        return returned_output.decode("utf-8")
    except Exception:
        pass

    # first check environment variable
    gdal_version = getenv("GDAL_VERSION")
    if gdal_version:
        return gdal_version

    logging.warning(
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
        except Exception:
            pass

    # from PyProj
    if pyproj is not None and PYPROJ_IS_AVAILABLE:
        try:
            proj_version = pyproj.__proj_version__
            logger.debug(f"Version de PROJ obtenue depuis PyProj : {proj_version}")
            return proj_version
        except Exception:
            pass

    # from PROJ command-line
    try:
        # Exécute la commande "proj" en utilisant subprocess
        result = subprocess.check_output(["proj"], stderr=subprocess.STDOUT, text=True)

        # Recherche de la version dans la sortie à l'aide d'une expression régulière
        if version_match := re.search(r"Rel\. ([0-9.]+)", result):
            proj_version = version_match.group(1)
            logger.debug(
                f"Version de PROJ obtenue depuis le binaire proj : {proj_version}"
            )
            return proj_version
        else:
            logger.error(
                "PROJ est bien installé mais impossible de trouver la version en regex."
            )
    except FileNotFoundError as err:
        logger.info(f"Proj n'est pas installé. Trace : {err}")
    except subprocess.CalledProcessError as e:
        logger.info(f"Erreur lors de l'exécution de la commande : {e}")

    # from environment variable
    if proj_version := getenv("PROJ_VERSION"):
        return proj_version

    logging.warning(
        "Impossible de déterminer la version de PROJ depuis les bindings GDAL, PyProj, "
        "les binaires proj ou la variable d'environnement PROJ_VERSION. "
    )
    return proj_version


# ############################################################################
# ##### Stand alone program ########
# ##################################

if __name__ == "__main__":
    """Standalone execution."""
    print(get_gdal_version())
    print(get_proj_version())
