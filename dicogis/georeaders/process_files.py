#! python3  # noqa: E265


# ##############################################################################
# ########## Libraries #############
# ##################################


# standard library
import logging
from collections.abc import Iterable
from dataclasses import dataclass
from locale import getlocale
from os import path
from pathlib import Path
from tkinter import IntVar, StringVar
from typing import Callable, Optional, Union

# package
from dicogis.constants import OutputFormats
from dicogis.export.base_serializer import MetadatasetSerializerBase
from dicogis.export.to_json import MetadatasetSerializerJson
from dicogis.export.to_xlsx import MetadatasetSerializerXlsx
from dicogis.georeaders.read_dxf import ReadCadDxf
from dicogis.georeaders.read_raster import ReadRasters
from dicogis.georeaders.read_vector_flat_dataset import ReadVectorFlatDataset
from dicogis.georeaders.read_vector_flat_geodatabase import ReadFlatDatabase
from dicogis.models.metadataset import MetaDataset
from dicogis.utils.texts import TextsManager
from dicogis.utils.utils import Utilities

# ##############################################################################
# ############ Globals ############
# #################################

txt_manager = TextsManager()
utils_global = Utilities()

# LOG
logger = logging.getLogger(__name__)

# ##############################################################################
# ############ Classes ############
# #################################


@dataclass
class DatasetToProcess:
    """Model of a geofile to process."""

    file_path: Path
    file_format: str
    georeader: object
    processed: bool = False
    process_error: Optional[str] = None
    exported: bool = False
    export_error: Optional[str] = None


class ProcessingFiles:
    """Geofiles processor."""

    MATRIX_FORMAT_GEOREADER = {
        "dxf": ReadCadDxf,
        "esri_shapefile": ReadVectorFlatDataset,
        "file_geodatabase_esri": ReadFlatDatabase,
        "file_geodatabase_spatialite": ReadFlatDatabase,
        "file_geodatabase_geopackage": ReadFlatDatabase,
        "geotiff": ReadRasters,
        "gxt": ReadVectorFlatDataset,
        "geojson": ReadVectorFlatDataset,
        "gml": ReadVectorFlatDataset,
        "kml": ReadVectorFlatDataset,
        "mapinfo_tab": ReadVectorFlatDataset,
        "raster": ReadRasters,
    }

    def __init__(
        self,
        format_or_serializer: OutputFormats | MetadatasetSerializerBase,
        localized_strings: Optional[dict],
        # input lists of files to process
        li_cdao: Optional[Iterable],
        li_dxf: Optional[Iterable],
        li_flat_geodatabase_esri_filegdb: Optional[Iterable],
        li_flat_geodatabase_geopackage: Optional[Iterable],
        li_flat_geodatabase_spatialite: Optional[Iterable],
        li_geojson: Optional[Iterable],
        li_geotiff: Optional[Iterable],
        li_gxt: Optional[Iterable],
        li_gml: Optional[Iterable],
        li_kml: Optional[Iterable],
        li_mapinfo_tab: Optional[Iterable],
        li_shapefiles: Optional[Iterable],
        li_vectors: Optional[Iterable],
        li_rasters: Optional[Iterable],
        li_file_databases: Optional[Iterable],
        # options
        opt_analyze_esri_filegdb: bool = True,
        opt_analyze_geojson: bool = True,
        opt_analyze_geopackage: bool = True,
        opt_analyze_geotiff: bool = True,
        opt_analyze_gml: bool = True,
        opt_analyze_gxt: bool = True,
        opt_analyze_kml: bool = True,
        opt_analyze_mapinfo_tab: bool = True,
        opt_analyze_raster: bool = True,
        opt_analyze_cdao: bool = True,
        opt_analyze_shapefiles: bool = True,
        opt_analyze_spatialite: bool = True,
        # progress
        progress_message_displayer: Optional[StringVar] = None,
        progress_counter: Optional[IntVar] = None,
        progress_callback_cmd: Optional[Callable] = None,
        # misc
        opt_quick_fail: bool = False,
    ) -> None:
        # -- STORE PARAMETERS AS ATTRIBUTES --
        self.serializer = self.serializer_from_output_format(format_or_serializer)

        # List of files
        self.li_dxf = li_dxf
        self.li_flat_geodatabase_esri_filegdb = li_flat_geodatabase_esri_filegdb
        self.li_flat_geodatabase_geopackage = li_flat_geodatabase_geopackage
        self.li_flat_geodatabase_spatialite = li_flat_geodatabase_spatialite
        self.li_geojson = li_geojson
        self.li_geotiff = li_geotiff
        self.li_gxt = li_gxt
        self.li_gml = li_gml
        self.li_kml = li_kml
        self.li_mapinfo_tab = li_mapinfo_tab
        self.li_shapefiles = li_shapefiles

        # list by family (= output tab)
        self.li_cdao = li_cdao
        self.li_file_databases = li_file_databases
        self.li_rasters = li_rasters
        self.li_vectors = li_vectors

        # Analisis options
        self.opt_analyze_esri_filegdb = opt_analyze_esri_filegdb
        self.opt_analyze_geojson = opt_analyze_geojson
        self.opt_analyze_gml = opt_analyze_gml
        self.opt_analyze_gxt = opt_analyze_gxt
        self.opt_analyze_kml = opt_analyze_kml
        self.opt_analyze_mapinfo_tab = opt_analyze_mapinfo_tab
        self.opt_analyze_raster = opt_analyze_raster
        self.opt_analyze_cdao = opt_analyze_cdao
        self.opt_analyze_shapefiles = opt_analyze_shapefiles
        self.opt_analyze_spatialite = opt_analyze_spatialite
        self.opt_analyze_esri_filegdb = opt_analyze_esri_filegdb
        self.opt_analyze_geojson = opt_analyze_geojson
        self.opt_analyze_geotiff = opt_analyze_geotiff
        self.opt_analyze_gml = opt_analyze_gml
        self.opt_analyze_gxt = opt_analyze_gxt
        self.opt_analyze_kml = opt_analyze_kml
        self.opt_analyze_mapinfo_tab = opt_analyze_mapinfo_tab
        self.opt_analyze_raster = opt_analyze_raster
        self.opt_analyze_cdao = opt_analyze_cdao
        self.opt_analyze_shapefiles = opt_analyze_shapefiles
        self.opt_analyze_geopackage = opt_analyze_geopackage

        # others
        self.opt_quick_fail = opt_quick_fail
        self.total_files: Optional[int] = None
        self.li_files_to_process: list[Optional[DatasetToProcess]] = []
        self.localized_strings = localized_strings
        if self.localized_strings is None:
            self.localized_strings = txt_manager.load_texts(language_code=getlocale())

        # progress
        self.progress_message_displayer = progress_message_displayer
        self.progress_counter = progress_counter
        self.progress_callback_cmd = progress_callback_cmd

    def serializer_from_output_format(
        self, format_or_serializer: OutputFormats | MetadatasetSerializerBase
    ) -> Union[MetadatasetSerializerJson, MetadatasetSerializerXlsx]:
        if isinstance(format_or_serializer, MetadatasetSerializerBase):
            return format_or_serializer

        if (
            isinstance(format_or_serializer, OutputFormats)
            and format_or_serializer.value == "excel"
        ):
            return MetadatasetSerializerXlsx
        elif (
            isinstance(format_or_serializer, OutputFormats)
            and format_or_serializer.value == "json"
        ):
            return MetadatasetSerializerJson

    def process_datasets_in_queue(self):
        """Process datasets in queue."""
        for geofile in self.li_files_to_process:
            if geofile.processed is True:
                logger.warning(f"File has already been processed: {geofile.file_path}")
                continue

            # extract dataset metadata
            geofile, metadataset = self.read_dataset(dataset_to_process=geofile)
            if metadataset is None:
                logger.error(
                    f"Reading {geofile.file_path} failed. It can't be serialized."
                )
                continue

            # storing informations into the output file
            geofile, metadataset = self.export_metadataset(
                dataset_to_process=geofile, metadataset_to_serialize=metadataset
            )

    def read_dataset(
        self, dataset_to_process: DatasetToProcess
    ) -> tuple[DatasetToProcess, MetaDataset | None]:
        """Read dataset and store into metadataset.

        Args:
            dataset_to_process: dataset path or URI to read

        Returns:
            dataset and metadataset, None if an error occurs
        """
        metadataset = None

        if self.opt_quick_fail:
            self.update_progress(
                message_to_display=f"Reading {dataset_to_process.file_path}..."
            )
            metadataset = dataset_to_process.georeader().infos_dataset(
                source_path=path.abspath(dataset_to_process.file_path),
            )
            logger.debug(f"Reading {dataset_to_process} succeeded.")
            self.update_progress(
                message_to_display=f"Reading {dataset_to_process.file_path}: OK",
                increment_counter=True,
            )
            dataset_to_process.processed = True
            return dataset_to_process, metadataset

        try:
            self.update_progress(
                message_to_display=f"Reading {dataset_to_process.file_path}..."
            )
            metadataset = dataset_to_process.georeader().infos_dataset(
                source_path=path.abspath(dataset_to_process.file_path),
            )
            logger.debug(f"Reading {dataset_to_process} succeeded.")
            self.update_progress(
                message_to_display=f"Reading {dataset_to_process.file_path}: OK",
                increment_counter=True,
            )
            dataset_to_process.processed = True
        except Exception as err:
            self.update_progress(
                message_to_display=f"Reading {dataset_to_process.file_path}: FAIL"
            )
            logger.error(
                f"Reading {dataset_to_process.file_path} "
                f"(format: {dataset_to_process.file_format}) failed. Trace: {err}"
            )
            dataset_to_process.processed = True
            dataset_to_process.process_error = err

        return dataset_to_process, metadataset

    def export_metadataset(
        self,
        dataset_to_process: DatasetToProcess,
        metadataset_to_serialize: MetaDataset,
    ) -> tuple[DatasetToProcess, MetaDataset | None]:
        self.serializer.serialize_metadaset(metadataset=metadataset_to_serialize)
        if self.opt_quick_fail:
            self.update_progress(
                message_to_display="Exporting metadata of "
                f"{dataset_to_process.file_path}..."
            )
            # writing to the Excel file
            self.update_progress(
                message_to_display="Exporting metadata of "
                f"{dataset_to_process.file_path}: OK",
                increment_counter=True,
            )
            logger.debug(f"Exporting metadata of {dataset_to_process.file_path}: OK")
            dataset_to_process.exported = True
            return dataset_to_process, metadataset_to_serialize

        try:
            self.update_progress(
                message_to_display="Exporting metadata of "
                f"{dataset_to_process.file_path}..."
            )
            # writing to the Excel file
            self.update_progress(
                message_to_display="Exporting metadata of "
                f"{dataset_to_process.file_path}: OK",
                increment_counter=True,
            )
            logger.debug(f"Exporting metadata of {dataset_to_process.file_path}: OK")
            dataset_to_process.exported = True
        except Exception as err:
            dataset_to_process.exported = False
            dataset_to_process.exported = err
            logger.error(
                f"Exporting metadata of {dataset_to_process.file_path} failed. "
                f"Trace: {err}"
            )

        return dataset_to_process, metadataset_to_serialize

    def add_files_to_process_queue(
        self, list_of_datasets: list, dataset_format: str
    ) -> list[DatasetToProcess]:
        """Add dataset to the processing queue.

        Args:
            list_of_datasets: list of datasets where to register the dataets
            dataset_format: _description_

        Returns:
            _description_
        """
        out_list: list = []

        for geofile in list_of_datasets:
            out_list.append(
                DatasetToProcess(
                    file_path=geofile,
                    file_format=dataset_format,
                    georeader=self.MATRIX_FORMAT_GEOREADER.get(dataset_format),
                )
            )

        self.li_files_to_process.extend(out_list)
        logger.debug(
            f"{len(out_list)} files (format: {dataset_format}) added to the "
            "process queue."
        )
        return out_list

    def count_files_to_process(self) -> int:
        total_files: int = 0
        if self.opt_analyze_shapefiles and len(self.li_shapefiles):
            total_files += len(self.li_shapefiles)
            self.serializer.pre_serializing(has_vector=1)
            self.add_files_to_process_queue(
                list_of_datasets=self.li_shapefiles, dataset_format="esri_shapefile"
            )

        if self.opt_analyze_mapinfo_tab and len(self.li_mapinfo_tab):
            total_files += len(self.li_mapinfo_tab)
            self.serializer.pre_serializing(has_vector=1)
            self.add_files_to_process_queue(
                list_of_datasets=self.li_mapinfo_tab, dataset_format="mapinfo_tab"
            )

        if self.opt_analyze_kml and len(self.li_kml):
            total_files += len(self.li_kml)
            self.serializer.pre_serializing(has_vector=1)
            self.add_files_to_process_queue(
                list_of_datasets=self.li_kml, dataset_format="kml"
            )

        if self.opt_analyze_gml and len(self.li_gml):
            total_files += len(self.li_gml)
            self.serializer.pre_serializing(has_vector=1)
            self.add_files_to_process_queue(
                list_of_datasets=self.li_gml, dataset_format="gml"
            )

        if self.opt_analyze_geojson and len(self.li_geojson):
            total_files += len(self.li_geojson)
            self.serializer.pre_serializing(has_vector=1)
            self.add_files_to_process_queue(
                list_of_datasets=self.li_geojson, dataset_format="geojson"
            )

        if self.opt_analyze_geotiff and len(self.li_geotiff):
            total_files += len(self.li_geotiff)
            self.serializer.pre_serializing(has_raster=1)
            self.add_files_to_process_queue(
                list_of_datasets=self.li_geotiff, dataset_format="geotiff"
            )

        if self.opt_analyze_gxt and len(self.li_gxt):
            total_files += len(self.li_gxt)
            self.serializer.pre_serializing(has_vector=1)
            self.add_files_to_process_queue(
                list_of_datasets=self.li_gxt, dataset_format="gxt"
            )

        if self.opt_analyze_raster and len(self.li_rasters):
            total_files += len(self.li_rasters)
            self.serializer.pre_serializing(has_raster=1)
            self.add_files_to_process_queue(
                list_of_datasets=self.li_tif, dataset_format="raster"
            )

        if self.opt_analyze_esri_filegdb and len(self.li_flat_geodatabase_esri_filegdb):
            total_files += len(self.li_flat_geodatabase_esri_filegdb)
            self.serializer.pre_serializing(has_filedb=1)
            self.add_files_to_process_queue(
                list_of_datasets=self.li_flat_geodatabase_esri_filegdb,
                dataset_format="file_geodatabase_esri",
            )

        if self.opt_analyze_geopackage and len(self.li_flat_geodatabase_geopackage):
            total_files += len(self.li_flat_geodatabase_geopackage)
            self.serializer.pre_serializing(has_filedb=1)
            self.add_files_to_process_queue(
                list_of_datasets=self.li_flat_geodatabase_geopackage,
                dataset_format="file_geodatabase_geopackage",
            )

        if self.opt_analyze_spatialite and len(self.li_flat_geodatabase_spatialite):
            total_files += len(self.li_flat_geodatabase_spatialite)
            self.serializer.pre_serializing(has_filedb=1)
            self.add_files_to_process_queue(
                list_of_datasets=self.li_flat_geodatabase_spatialite,
                dataset_format="file_geodatabase_spatialite",
            )

        if self.opt_analyze_cdao and len(self.li_cdao):
            total_files += len(self.li_cdao)
            self.serializer.pre_serializing(has_cad=1)
            self.add_files_to_process_queue(
                list_of_datasets=self.li_cdao, dataset_format="file_cad"
            )

        self.total_files = total_files
        return total_files

    def update_progress(
        self, message_to_display: str | None = None, increment_counter: bool = False
    ):
        """Helper method to update progress bar/status/counter.

        Args:
            message_to_display: message to display. Defaults to None.
            increment_counter: option to increment progress counter. Defaults to False.
        """
        if hasattr(self.progress_message_displayer, "set"):
            self.progress_message_displayer.set(message_to_display)
        if increment_counter and self.progress_counter is not None:
            if hasattr(self.progress_counter, "set") and hasattr(
                self.progress_counter, "get"
            ):
                self.progress_counter.set(self.progress_counter.get() + 1)
            else:
                self.progress_counter += 1
        if self.progress_callback_cmd is not None:
            self.progress_callback_cmd()
