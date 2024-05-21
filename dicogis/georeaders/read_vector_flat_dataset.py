#! python3  # noqa: E265

"""
    Name:         InfosSHP
    Purpose:      Use GDAL/OGR library to extract informations about
                       geographic data. It permits a more friendly use as
                       submodule.

    Author:       Julien Moura (https://github.com/Guts/)
"""

# ############################################################################
# ######### Libraries #############
# #################################

# Standard library
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

# package
from dicogis.georeaders.base_georeader import GeoReaderBase
from dicogis.models.dataset import MetaVectorDataset
from dicogis.utils.check_path import check_var_can_be_path

# 3rd party libraries


# ############################################################################
# ######### Globals ############
# ##############################

logger = logging.getLogger(__name__)


# ############################################################################
# ######### Classes #############
# ###############################


class ReadVectorFlatDataset(GeoReaderBase):
    """Reader for geographic dataset stored as flat vector files."""

    def __init__(self):
        """Class constructor."""
        super().__init__(dataset_type="flat_vector")

    def infos_dataset(
        self,
        source_path: Union[Path, str],
        metadataset: Optional[MetaVectorDataset] = None,
        tipo: Optional[str] = None,
    ):
        """Use OGR functions to extract basic informations about
        geographic vector file (handles shapefile or MapInfo tables)
        and store into dictionaries.

        source_path = path to the geographic file
        dico_dataset = dictionary for global informations
        tipo = format

        """
        if isinstance(source_path, str):
            check_var_can_be_path(input_var=source_path, raise_error=True)
            source_path = Path(source_path).resolve()

        if metadataset is None:
            metadataset = MetaVectorDataset(
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

        # get the layer
        layer = dataset.GetLayer()

        # dependencies and total size
        metadataset.files_dependencies = self.list_dependencies(
            main_dataset=source_path
        )
        metadataset.storage_size = self.calc_size_full_dataset(
            source_path=source_path, dependencies=metadataset.files_dependencies
        )
        # Getting basic dates
        metadataset.storage_date_created = datetime.fromtimestamp(
            source_path.stat().st_ctime
        )
        metadataset.storage_date_updated = datetime.fromtimestamp(
            source_path.stat().st_mtime
        )

        # features
        metadataset.features_count = layer.GetFeatureCount()
        if metadataset.features_count == 0:
            """if layer doesn't have any object, return an error"""
            self.counter_alerts += 1
            self.erratum(
                target_container=metadataset,
                source_path=source_path,
                err_type="err_nobjet",
            )

        # fields
        layer_def = layer.GetLayerDefn()
        metadataset.attribute_fields_count = layer_def.GetFieldCount()
        metadataset.attribute_fields = self.get_fields_details(
            ogr_layer_definition=layer_def
        )

        # geometry type
        layer_geom_type = self.get_geometry_type(layer)
        if layer_geom_type is None:
            metadataset.processing_error_msg += f"{self.gdal_err.err_msg} -- "
            metadataset.processing_error_type += f"{self.gdal_err.err_type} -- "
            metadataset.processing_succeeded = False
        metadataset.geometry_type = layer_geom_type

        # SRS
        srs_details = self.get_srs_details(layer)
        metadataset.crs_name = srs_details[0]
        metadataset.crs_registry_code = srs_details[1]
        metadataset.crs_type = srs_details[2]

        # spatial extent
        metadataset.bbox = self.get_extent_as_tuple(ogr_layer=layer)

        # warnings messages
        if self.counter_alerts:
            metadataset.processing_succeeded = False
            metadataset.processing_error_msg = self.gdal_err.err_msg
            metadataset.processing_error_type = self.gdal_err.err_type

        # clean & exit
        del dataset
        return metadataset
