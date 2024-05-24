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

# 3rd party
from osgeo import ogr

# package
from dicogis.georeaders.base_georeader import GeoReaderBase
from dicogis.models.metadataset import MetaDatabaseFlat, MetaVectorDataset
from dicogis.utils.check_path import check_var_can_be_path

# ############################################################################
# ######### Globals ############
# ##############################

logger = logging.getLogger(__name__)


# ############################################################################
# ######### Classes #############
# ###############################


class ReadVectorFlatDataset(GeoReaderBase):
    """Reader for geographic dataset stored as flat vector files."""

    def __init__(self, dataset_type="flat_vector"):
        """Class constructor."""
        super().__init__(dataset_type=dataset_type)

    def infos_dataset(
        self,
        source_path: Union[Path, str],
        metadataset: Optional[MetaVectorDataset] = None,
        fallback_format: Optional[str] = None,
    ) -> MetaVectorDataset | MetaDatabaseFlat:
        """Get metadata from dataset.

        Args:
            source_path (Union[Path, str]): path to the dataset file.
            metadataset (Optional[MetaVectorDataset], optional): metadataset object to
                fill. Defaults to None.
            fallback_format (Optional[str], optional): format name used as fallback if
                GDAL fails to open the dataset. Defaults to None.

        Returns:
            MetaVectorDataset: metadataset object
        """

        if isinstance(source_path, str):
            check_var_can_be_path(input_var=source_path, raise_error=True)
            source_path = Path(source_path).resolve()

        if metadataset is None:
            if self.dataset_type == "flat_vector":
                metadataset = MetaVectorDataset(
                    path=source_path,
                    name=source_path.stem,
                    parent_folder_name=source_path.parent.name,
                    dataset_type=self.dataset_type,
                )
            elif self.dataset_type == "flat_database":

                metadataset = MetaDatabaseFlat(
                    path=source_path,
                    name=source_path.stem,
                    parent_folder_name=source_path.parent.name,
                    dataset_type=self.dataset_type,
                )

        # opening dataset
        try:
            dataset = self.open_dataset_with_gdal(source_dataset=source_path)
        except Exception as err:
            logger.error(f"An error occurred opening '{source_path}'. Trace: {err}")
            self.counter_alerts = self.counter_alerts + 1
            metadataset.format_gdal_long_name = fallback_format
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

        # get layer(s) informations
        if self.dataset_type == "flat_vector" and dataset.GetLayerCount() == 1:
            self.get_infos_layer(in_layer=dataset.GetLayer(), metadataset=metadataset)
        elif self.dataset_type == "flat_database":
            metadataset.layers_count = dataset.GetLayerCount()
            metadataset.layers = []
            for layer_idx in range(dataset.GetLayerCount()):
                layer: ogr.Layer = dataset.GetLayer(layer_idx)
                layer_metadataset = MetaVectorDataset(
                    name=layer.GetName(), dataset_type="data_layer"
                )
                self.get_infos_layer(in_layer=layer, metadataset=layer_metadataset)
                metadataset.layers.append(layer_metadataset)

        # warnings messages
        if self.counter_alerts:
            metadataset.processing_succeeded = False
            metadataset.processing_error_msg = self.gdal_err.err_msg
            metadataset.processing_error_type = self.gdal_err.err_type

        # clean & exit
        del dataset
        return metadataset

    def get_infos_layer(self, in_layer: ogr.Layer, metadataset: MetaVectorDataset):
        # features
        metadataset.features_objects_count = in_layer.GetFeatureCount()
        if metadataset.features_objects_count == 0:
            """if layer doesn't have any object, return an error"""
            self.counter_alerts += 1
            self.erratum(
                target_container=metadataset,
                src_dataset_layer=in_layer,
                err_type="err_nobjet",
            )

        # fields
        layer_def = in_layer.GetLayerDefn()
        metadataset.feature_attributes = self.get_fields_details(
            ogr_layer_definition=layer_def
        )

        # geometry type
        layer_geom_type = self.get_geometry_type(in_layer)
        if layer_geom_type is None:
            metadataset.processing_error_msg += f"{self.gdal_err.err_msg} -- "
            metadataset.processing_error_type += f"{self.gdal_err.err_type} -- "
            metadataset.processing_succeeded = False
        metadataset.geometry_type = layer_geom_type

        # SRS
        srs_details = self.get_srs_details(in_layer)
        metadataset.crs_name = srs_details[0]
        metadataset.crs_registry_code = srs_details[1]
        metadataset.crs_type = srs_details[2]

        # spatial extent
        metadataset.bbox = self.get_extent_as_tuple(dataset_or_layer=in_layer)


# ###########################################################################
# #### Stand alone program ########
# #################################
if __name__ == "__main__":
    """Standalone execution."""
    from pprint import pprint

    # Shapefile
    georeader = ReadVectorFlatDataset()
    metadataset = georeader.infos_dataset(
        source_path="tests/fixtures/gisdata/data/good/vector/san_andres_y_providencia_coastline.shp",
    )
    pprint(metadataset)

    # SpatiaLite
    georeader = ReadVectorFlatDataset(dataset_type="flat_database")
    metadataset = georeader.infos_dataset(
        source_path="/home/jmo/Documents/GIS Database/QGIS Training Data/QGIS-Training-Data-release_3.28/exercise_data/qgis-server-tutorial-data/naturalearth.sqlite",
    )
    pprint(metadataset)

    # Geopackage
    georeader = ReadVectorFlatDataset(dataset_type="flat_database")
    metadataset = georeader.infos_dataset(
        source_path="/home/jmo/Documents/GIS Database/SIRAD/SIRAD_2012.gpkg"
    )
    pprint(metadataset)

    # Esri FileGDB
    georeader = ReadVectorFlatDataset(dataset_type="flat_database")
    metadataset = georeader.infos_dataset(
        source_path="/home/jmo/Documents/GIS Database/SIRAD/SIRAD_2012.gdb"
    )
    pprint(metadataset)
