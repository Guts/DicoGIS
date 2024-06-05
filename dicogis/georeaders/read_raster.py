#! python3  # noqa: E265

# ############################################################################
# ######### Libraries #############
# #################################

# Standard library
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

# 3rd party libraries
from osgeo import gdal

# package
from dicogis.georeaders.base_georeader import GeoReaderBase
from dicogis.models.metadataset import MetaRasterDataset
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
        """Initialize module."""
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

        # Getting basic dates
        metadataset.storage_date_created = datetime.fromtimestamp(
            source_path.stat().st_ctime
        )
        metadataset.storage_date_updated = datetime.fromtimestamp(
            source_path.stat().st_mtime
        )

        # dependencies and total size
        metadataset.files_dependencies = self.list_dependencies(main_dataset=dataset)
        metadataset.storage_size = self.calc_size_full_dataset(
            source_path=source_path, dependencies=metadataset.files_dependencies
        )

        # SRS
        (
            metadataset.crs_name,
            metadataset.crs_registry,
            metadataset.crs_registry_code,
            metadataset.crs_type,
        ) = self.get_srs_details(dataset_or_layer=dataset)

        # basic informations
        dataset_gdal_metadata = dataset.GetMetadata()
        metadataset.compression_rate = dataset_gdal_metadata.get(
            "COMPRESSION_RATE_TARGET"
        )
        metadataset.color_space = dataset_gdal_metadata.get("COLORSPACE")

        # image specifications
        metadataset.columns_count = dataset.RasterXSize
        metadataset.rows_count = dataset.RasterYSize
        metadataset.bands_count = dataset.RasterCount

        # data type
        metadataset.data_type = gdal.GetDataTypeName(dataset.GetRasterBand(1).DataType)

        # geometry information
        metadataset.bbox = self.get_extent_as_tuple(dataset_or_layer=dataset)
        geotransform = self.rast.GetGeoTransform()
        metadataset.origin_x = geotransform[0]
        metadataset.origin_y = geotransform[3]
        metadataset.pixel_width = round(geotransform[1], 3)
        metadataset.pixel_height = round(geotransform[5], 3)
        metadataset.orientation = geotransform[2]

        # warnings messages
        if self.counter_alerts:
            metadataset.processing_succeeded = False
            metadataset.processing_error_msg = self.gdal_err.err_msg
            metadataset.processing_error_type = self.gdal_err.err_type

        # safe close (see: http://pcjericks.github.io/py-gdalogr-cookbook/)
        del dataset

        return metadataset
