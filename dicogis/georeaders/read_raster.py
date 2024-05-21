#! python3  # noqa: E265

# ############################################################################
# ######### Libraries #############
# #################################

# Standard library
import logging
from os import path
from pathlib import Path
from time import localtime, strftime
from typing import Optional, Union

# 3rd party libraries
from osgeo import gdal, osr

# package
from dicogis.georeaders.base_georeader import GeoReaderBase
from dicogis.models.dataset import MetaRasterDataset
from dicogis.utils.check_path import check_var_can_be_path

# ############################################################################
# ######### Globals ############
# ##############################

logger = logging.getLogger(__name__)

# ############################################################################
# ######### Classes #############
# #################################


class ReadRasters(GeoReaderBase):
    """Reader for geographic dataset stored as flat raster files."""

    def __init__(
        self,
    ):
        """Initialization."""
        super().__init__(dataset_type="flat_raster")

    def infos_dataset(
        self,
        source_path: Union[Path, str],
        metadataset: Optional[MetaRasterDataset] = None,
        tipo: Optional[str] = None,
    ):
        if isinstance(source_path, str):
            check_var_can_be_path(input_var=source_path, raise_error=True)
            source_path = Path(source_path).resolve()

        if metadataset is None:
            metadataset = MetaRasterDataset(
                path=source_path,
                name=source_path.stem,
                parent_folder_name=source_path.parent.name,
            )

        # opening dataset
        try:
            dataset = self.open_dataset_with_gdal(source_dataset=source_path)
        except Exception as err:
            logger.error(f"An error occurred opening '{source_path}'. Trace: {err}")
            self.counter_alerts = self.counter_alerts + 1
            metadataset.format_gdal_long_name = tipo
            self.erratum(
                target_container=metadataset,
                src_path=source_path,
                err_type="err_corrupt",
            )
            metadataset.processing_succeeded = False
            metadataset.processing_error_type = self.gdal_err.err_type
            metadataset.processing_error_msg = self.gdal_err.err_msg
            return metadataset

        metadataset.format_gdal_long_name = dataset.GetDriver().LongName
        metadataset.format_gdal_short_name = dataset.GetDriver().ShortName

        # raising incompatible files
        if not dataset:
            """if file is not compatible"""
            self.counter_alerts += 1
            metadataset.processing_succeeded = False
            metadataset.processing_error_type = self.gdal_err.err_type
            metadataset.processing_error_msg = self.gdal_err.err_msg
            self.erratum(
                target_container=metadataset,
                src_path=source_path,
                err_type="err_nobjet",
            )
            return metadataset

        # basic informations
        self.infos_basics(source_path, dico_raster, self.localized_strings)

        # geometry information
        self.infos_geom(dico_raster, self.localized_strings)

        # bands information
        for band in range(1, self.rast.RasterCount):
            self.infos_bands(band, dico_bands)
            band = None

        # safe close (see: http://pcjericks.github.io/py-gdalogr-cookbook/)
        del self.rast
        # warnings messages
        dico_raster["err_gdal"] = self.gdalerr.err_type, self.gdalerr.err_msg

    def infos_basics(self, rasterpath, dico_raster):
        """Get the global informations about the raster."""

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
    textos = {}
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
        dico_raster = {}  # dictionary where will be stored informations
        dico_bands = {}  # dictionary for fields information
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
