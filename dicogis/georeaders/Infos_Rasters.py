#! python3  # noqa: E265


# ----------------------------------------------------------------------------
# Name:         Infos Rasters
# Purpose:      Use GDAL library to extract informations about
#                   geographic rasters data. It permits a more friendly use as
#                   submodule.
#
# Author:       Julien Moura (https://github.com/Guts/)
# ----------------------------------------------------------------------------


# ############################################################################
# ######### Libraries #############
# #################################
# Standard library
import logging
from collections import OrderedDict
from os import chdir, path
from time import localtime, strftime

# 3rd party libraries
try:
    from osgeo import gdal, osr
    from osgeo.gdalconst import GA_ReadOnly
except ImportError:
    import gdal
    import osr
    from gdalconst import GA_ReadOnly

# ############################################################################
# ######### Globals ############
# ##############################

logger = logging.getLogger(__name__)

# ############################################################################
# ######### Classes #############
# #################################


class GdalErrorHandler:
    def __init__(self):
        """Callable error handler.

        see: http://trac.osgeo.org/gdal/wiki/PythonGotchas#Exceptionsraisedincustomerrorhandlersdonotgetcaught
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

        # disabling GDAL exceptions raising to avoid future troubles
        gdal.DontUseExceptions()

        # propagating
        self.err_level = err_level
        self.err_type = err_type
        self.err_msg = err_msg

        # end of function
        return self.err_level, self.err_type, self.err_msg


class ReadRasters:
    def __init__(self, rasterpath, dico_raster, dico_bands, tipo, text=""):
        """Use GDAL functions to extract basic informations about
        geographic raster file (handles ECW, GeoTIFF, JPEG2000)
        and store into dictionaries.

        layerpath = path to the geographic file
        dico_raster = dictionary for global informations
        dico_bands = dictionary for the bands informations
        tipo = format
        text = dictionary of text in the selected language
        """
        # gdal specific
        gdal.AllRegister()
        # changing working directory to layer folder
        chdir(path.dirname(rasterpath))

        # handling specific exceptions
        gdalerr = GdalErrorHandler()
        errhandler = gdalerr.handler
        gdal.PushErrorHandler(errhandler)
        self.alert = 0
        # gdal.SetConfigOption(str("GTIFF_IGNORE_READ_ERRORS"), str("TRUE"))
        gdal.UseExceptions()

        # opening file
        try:
            self.rast = gdal.Open(rasterpath, GA_ReadOnly)
        except Exception as err:
            logger.error(err)
            self.alert += 1
            self.erratum(dico_raster, rasterpath, "err_incomp")
            return

        # check if raster is GDAL friendly
        if self.rast is None:
            self.alert += 1
            self.erratum(dico_raster, rasterpath, "err_incomp")
            return
        else:
            pass
        # basic informations
        dico_raster["format"] = tipo
        self.infos_basics(rasterpath, dico_raster, text)
        # geometry information
        self.infos_geom(dico_raster, text)
        # bands information
        for band in range(1, self.rast.RasterCount):
            self.infos_bands(band, dico_bands)
            band = None

        # safe close (see: http://pcjericks.github.io/py-gdalogr-cookbook/)
        del self.rast
        # warnings messages
        dico_raster["err_gdal"] = gdalerr.err_type, gdalerr.err_msg

    def infos_basics(self, rasterpath, dico_raster, txt):
        """Get the global informations about the raster."""
        # files and folder
        dico_raster["name"] = path.basename(rasterpath)
        dico_raster["folder"] = path.dirname(rasterpath)
        dico_raster["title"] = dico_raster["name"][:-4].replace("_", " ").capitalize()

        # dependencies
        dependencies = [
            path.basename(filedepend)
            for filedepend in self.rast.GetFileList()
            if filedepend != rasterpath
        ]
        dico_raster["dependencies"] = dependencies

        # total size
        dependencies.append(rasterpath)
        dico_raster["total_size"] = sum([path.getsize(f) for f in dependencies])
        dependencies.pop(-1)

        # format
        rastMD = self.rast.GetMetadata()
        dico_raster["compr_rate"] = rastMD.get("COMPRESSION_RATE_TARGET")
        dico_raster["color_ref"] = rastMD.get("COLORSPACE")
        if rastMD.get("VERSION"):
            dico_raster["format_version"] = "(v{})".format(rastMD.get("VERSION"))
        else:
            dico_raster["format_version"] = ""
        # image specifications
        dico_raster["num_cols"] = self.rast.RasterXSize
        dico_raster["num_rows"] = self.rast.RasterYSize
        dico_raster["num_bands"] = self.rast.RasterCount

        # data type
        dico_raster["data_type"] = gdal.GetDataTypeName(
            self.rast.GetRasterBand(1).DataType
        )

        # basic dates
        dico_raster["date_actu"] = strftime(
            "%d/%m/%Y", localtime(path.getmtime(rasterpath))
        )
        dico_raster["date_crea"] = strftime(
            "%d/%m/%Y", localtime(path.getctime(rasterpath))
        )

        # end of function
        return dico_raster

    def infos_geom(self, dico_raster, txt):
        """Get the informations about geometry."""
        # Spatial extent (bounding box)
        geotransform = self.rast.GetGeoTransform()
        dico_raster["xOrigin"] = geotransform[0]
        dico_raster["yOrigin"] = geotransform[3]
        dico_raster["pixelWidth"] = round(geotransform[1], 3)
        dico_raster["pixelHeight"] = round(geotransform[5], 3)
        dico_raster["orientation"] = geotransform[2]

        # -- SRS
        # using osr to get the srs
        srs = osr.SpatialReference(self.rast.GetProjection())
        # srs.ImportFromWkt(self.rast.GetProjection())
        srs.AutoIdentifyEPSG()

        # srs types
        srsmetod = [
            (srs.IsCompound(), txt.get("srs_comp")),
            (srs.IsGeocentric(), txt.get("srs_geoc")),
            (srs.IsGeographic(), txt.get("srs_geog")),
            (srs.IsLocal(), txt.get("srs_loca")),
            (srs.IsProjected(), txt.get("srs_proj")),
            (srs.IsVertical(), txt.get("srs_vert")),
        ]
        # searching for a match with one of srs types
        for srsmet in srsmetod:
            if srsmet[0] == 1:
                typsrs = srsmet[1]
            else:
                continue
        # in case of not match
        try:
            dico_raster["srs_type"] = typsrs
        except UnboundLocalError:
            typsrs = txt.get("srs_nr")
            dico_raster["srs_type"] = typsrs

        # Handling exception in srs names'encoding
        if srs.IsProjected():
            try:
                if srs.GetAttrValue("PROJCS") is not None:
                    dico_raster["srs"] = srs.GetAttrValue("PROJCS").replace("_", " ")
                else:
                    dico_raster["srs"] = srs.GetAttrValue("PROJECTION").replace(
                        "_", " "
                    )
            except UnicodeDecodeError:
                if srs.GetAttrValue("PROJCS") != "unnamed":
                    dico_raster["srs"] = (
                        srs.GetAttrValue("PROJCS").decode("latin1").replace("_", " ")
                    )
                else:
                    dico_raster["srs"] = (
                        srs.GetAttrValue("PROJECTION")
                        .decode("latin1")
                        .replace("_", " ")
                    )
        else:
            try:
                if srs.GetAttrValue("GEOGCS") is not None:
                    dico_raster["srs"] = srs.GetAttrValue("GEOGCS").replace("_", " ")
                else:
                    dico_raster["srs"] = srs.GetAttrValue(
                        "PROJECTION".replace("_", " ")
                    )
            except UnicodeDecodeError:
                if srs.GetAttrValue("GEOGCS") != "unnamed":
                    dico_raster["srs"] = (
                        srs.GetAttrValue("GEOGCS").decode("latin1").replace("_", " ")
                    )
                else:
                    dico_raster["srs"] = (
                        srs.GetAttrValue("PROJECTION")
                        .decode("latin1")
                        .replace("_", " ")
                    )

        dico_raster["epsg"] = srs.GetAttrValue("AUTHORITY", 1)

        # end of function
        return dico_raster

    def infos_bands(self, band, dico_bands):
        """Get the informations about fields definitions."""
        # getting band object
        band_info = self.rast.GetRasterBand(band)

        # band statistics
        try:
            stats = band_info.GetStatistics(True, True)
        except Exception as err:
            logger.error(err)
            return
        if stats:
            # band minimum value
            if band_info.GetMinimum() is None:
                dico_bands[f"band{band}_Min"] = stats[0]
            else:
                dico_bands[f"band{band}_Min"] = band_info.GetMinimum()

            # band maximum value
            if band_info.GetMinimum() is None:
                dico_bands[f"band{band}_Max"] = stats[1]
            else:
                dico_bands[f"band{band}_Max"] = band_info.GetMaximum()

            # band mean value
            dico_bands[f"band{band}_Mean"] = round(stats[2], 2)

            # band standard deviation value
            dico_bands[f"band{band}_Sdev"] = round(stats[3], 2)
        else:
            pass

        # band no data value
        dico_bands[f"band{band}_NoData"] = band_info.GetNoDataValue()

        # band scale value
        dico_bands[f"band{band}_Scale"] = band_info.GetScale()

        # band unit type value
        dico_bands[f"band{band}_UnitType"] = band_info.GetUnitType()

        # color table
        coul_table = band_info.GetColorTable()
        if coul_table is None:
            dico_bands[f"band{band}_CTabCount"] = 0
        else:
            dico_bands[f"band{band}_CTabCount"] = coul_table.GetCount()
            # -- COMENTED BECAUSE IT'S TOO MUCH INFORMATIONS
            # for ctab_idx in range(0, coul_table.GetCount()):
            #     entry = coul_table.GetColorEntry(ctab_idx)
            #     if not entry:
            #         continue
            #     else:
            #         pass
            #     dico_bands["band{0}_CTab{1}_RGB".format(band, ctab_idx)] = \
            #                   coul_table.GetColorEntryAsRGB(ctab_idx, entry)

        # safe close (quite useless but good practice to have)
        del stats
        del band_info

        # end of function
        return dico_bands

    def sizeof(self, os_size):
        """return size in different units depending on size
        see http://stackoverflow.com/a/1094933"""
        for size_cat in ["octets", "Ko", "Mo", "Go"]:
            if os_size < 1024.0:
                return f"{os_size:3.1f} {size_cat}"
            os_size /= 1024.0
        return "{:3.1f} {}".format(os_size, " To")

    def erratum(self, dico_raster, rasterpath, mess):
        """errors handling"""
        # storing minimal informations to give clues to solve later
        dico_raster["name"] = path.basename(rasterpath)
        dico_raster["folder"] = path.dirname(rasterpath)
        dico_raster["error"] = mess
        # End of function
        return dico_raster


# ############################################################################
# #### Stand alone program ########
# #################################

if __name__ == "__main__":
    """standalone execution for tests. Paths are relative considering a test
    within the official repository (https://github.com/Guts/DicoShapes/)"""
    # listing test files by formats
    li_ecw = [r"..\..\test\datatest\rasters\ECW\0468_6740.ecw"]  # ECW
    li_gtif = [
        r"..\..\test\datatest\rasters\GeoTiff\BDP_07_0621_0049_020_LZ1.tif",
        r"..\..\test\datatest\rasters\GeoTiff\TrueMarble_16km_2700x1350.tif",
        r"..\..\test\datatest\rasters\GeoTiff\ASTGTM_S17W069_dem.tif",
        r"..\..\test\datatest\rasters\GeoTiff\completo1-2.tif",
    ]  # GeoTIFF
    li_jpg2 = [r"..\..\test\datatest\rasters\JPEG2000\image_jpg2000.jp2"]  # JPEG2000
    li_rasters = (
        path.abspath(li_ecw[0]),
        path.abspath(li_gtif[0]),
        path.abspath(li_gtif[1]),
        path.abspath(li_gtif[2]),
        path.abspath(li_gtif[3]),
        path.abspath(li_jpg2[0]),
    )

    # test text dictionary
    textos = OrderedDict()
    textos["srs_comp"] = "Compound"
    textos["srs_geoc"] = "Geocentric"
    textos["srs_geog"] = "Geographic"
    textos["srs_loca"] = "Local"
    textos["srs_proj"] = "Projected"
    textos["srs_vert"] = "Vertical"
    textos["geom_point"] = "Point"
    textos["geom_ligne"] = "Line"
    textos["geom_polyg"] = "Polygon"

    # execution
    for raster in li_rasters:
        """looping on raster files"""
        # recipient datas
        dico_raster = OrderedDict()  # dictionary where will be stored informations
        dico_bands = OrderedDict()  # dictionary for fields information
        # getting the informations
        if not path.isfile(raster):
            print("\n\t==> File doesn't exist: " + raster)
            continue
        else:
            pass
        print(("\n======================\n\t", path.basename(raster)))
        # handling odd warnings
        info_raster = ReadRasters(
            path.abspath(raster),
            dico_raster,
            dico_bands,
            path.splitext(raster)[1],
            textos,
        )
        print(f"\n\n{dico_raster}\n{dico_bands}")

        # deleting dictionaries
        del dico_raster, dico_bands, raster
