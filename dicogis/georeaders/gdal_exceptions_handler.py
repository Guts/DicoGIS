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

# ##############################################################################
# ########## Classes ###############
# ##################################


class GdalErrorHandler(object):
    def __init__(self):
        """Callable error handler.

        see: https://gdal.org/api/python_gotchas.html
        and http://pcjericks.github.io/py-gdalogr-cookbook/gdal_general.html#install-gdal-ogr-error-handler
        """
        self.err_level = gdal.CE_None
        self.err_type = 0
        self.err_msg = ""

    def handler(self, err_level, err_type, err_msg):
        """Make errors messages more readable."""
        # available types
        err_class = {
            gdal.CE_None: "None",
            gdal.CE_Debug: "Debug",
            gdal.CE_Warning: "Warning",
            gdal.CE_Failure: "Failure",
            gdal.CE_Fatal: "Fatal",
        }
        # getting type
        err_type = err_class.get(err_type, "None")

        # cleaning message
        err_msg = err_msg.replace("\n", " ")

        # disabling OGR exceptions raising to avoid future troubles
        ogr.DontUseExceptions()

        # propagating
        self.err_level = err_level
        self.err_type = err_type
        self.err_msg = err_msg

        # end of function
        return self.err_level, self.err_type, self.err_msg
