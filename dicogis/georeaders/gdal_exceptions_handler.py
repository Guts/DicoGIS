#! python3  # noqa: E265


# ##############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import logging

# 3rd party libraries
from osgeo import gdal, ogr

# #############################################################################
# ########## Globals ###############
# ##################################

logger = logging.getLogger(__name__)
# handling GDAL/OGR specific exceptions
gdal.AllRegister()
ogr.UseExceptions()
gdal.UseExceptions()

# ##############################################################################
# ########## Classes ###############
# ##################################


class GdalErrorHandler:
    """Callable error handler.

    See:

    - https://gdal.org/api/python_gotchas.html
    - http://pcjericks.github.io/py-gdalogr-cookbook/gdal_general.html#install-gdal-ogr-error-handler
    - https://gis.stackexchange.com/a/91393
    """

    def __init__(self):
        """Object initialization."""
        self.err_level = gdal.CE_None
        self.err_type = 0
        self.err_msg = ""

    def handler(self, err_level: int, err_type: int, err_msg: str):
        """Make errors messages more readable."""

        # propagating
        self.err_level = err_level
        self.err_type = err_type
        self.err_msg = err_msg


if __name__ == "__main__":
    logging.basicConfig(
        format="%(levelname)s:%(asctime)s %(message)s",
        level=logging.INFO,
    )

    err = GdalErrorHandler()
    gdal.PushErrorHandler(err.handler)
    gdal.UseExceptions()  # Exceptions will get raised on anything >= gdal.CE_Failure

    try:
        gdal.Error(gdal.CE_Failure, 42, "Test error message")
    except Exception as err:
        logging.error(err)
