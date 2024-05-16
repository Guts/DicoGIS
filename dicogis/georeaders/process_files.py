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
from typing import Callable, Optional

# package
from dicogis.export.to_xlsx import MetadataToXlsx
from dicogis.georeaders.read_dxf import ReadDXF
from dicogis.georeaders.read_esri_filegdb import ReadEsriFileGdb
from dicogis.georeaders.read_gxt import ReadGXT
from dicogis.georeaders.read_raster import ReadRasters
from dicogis.georeaders.read_spatialite import ReadSpatialite
from dicogis.georeaders.read_vector_flat_dataset import ReadVectorFlatDataset
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
class FileToProcess:
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
        "dxf": ReadDXF,
        "esri_shapefile": ReadVectorFlatDataset,
        "file_geodatabase_esri": ReadEsriFileGdb,
        "file_geodatabase_spatialite": ReadSpatialite,
        "geotiff": ReadRasters,
        "gxt": ReadGXT,
        "geojson": ReadVectorFlatDataset,
        "gml": ReadVectorFlatDataset,
        "kml": ReadVectorFlatDataset,
        "mapinfo_tab": ReadVectorFlatDataset,
        "raster": ReadRasters,
    }

    def __init__(
        self,
        output_workbook: MetadataToXlsx,
        localized_strings: Optional[dict],
        # input lists of files to process
        li_cdao: Optional[Iterable],
        li_dxf: Optional[Iterable],
        li_filegdb_esri: Optional[Iterable],
        li_filegdb_spatialite: Optional[Iterable],
        li_geojson: Optional[Iterable],
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
        opt_analyze_gml: bool = True,
        opt_analyze_gxt: bool = True,
        opt_analyze_kml: bool = True,
        opt_analyze_mapinfo_tab: bool = True,
        opt_analyze_raster: bool = True,
        opt_analyze_cdao: bool = True,
        opt_analyze_shapefiles: bool = True,
        opt_analyze_spatialite: bool = True,
    ) -> None:
        # -- STORE PARAMETERS AS ATTRIBUTES --
        self.output_workbook = output_workbook

        # List of files
        self.li_dxf = li_dxf
        self.li_filegdb_esri = li_filegdb_esri
        self.li_filegdb_spatialite = li_filegdb_spatialite
        self.li_geojson = li_geojson
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
        self.opt_analyze_gml = opt_analyze_gml
        self.opt_analyze_gxt = opt_analyze_gxt
        self.opt_analyze_kml = opt_analyze_kml
        self.opt_analyze_mapinfo_tab = opt_analyze_mapinfo_tab
        self.opt_analyze_raster = opt_analyze_raster
        self.opt_analyze_cdao = opt_analyze_cdao
        self.opt_analyze_shapefiles = opt_analyze_shapefiles
        self.opt_analyze_spatialite = opt_analyze_spatialite

        # others
        self.total_files: Optional[int] = None
        self.li_files_to_process: list[Optional[FileToProcess]] = []
        self.localized_strings = localized_strings
        if self.localized_strings is None:
            txt_manager.load_texts(
                dico_texts=localized_strings, language_code=getlocale()[0]
            )

    def process_files_in_queue(
        self,
        progress_value_message: Optional[str] = None,
        progress_value_count: Optional[int] = None,
        progress_callback_cmd: Optional[Callable] = None,
    ) -> bool:
        for geofile in self.li_files_to_process:
            if geofile.processed is True:
                logger.warning(f"File has already been processed: {geofile.file_path}")
                continue

            # progression
            logger.info(f"Processing: {geofile}")
            if progress_value_message is not None:
                if hasattr(progress_value_message, "set"):
                    progress_value_message.set(
                        f"Reading: {Path(geofile.file_path).name}"
                    )
                else:
                    progress_value_message = f"Reading: {Path(geofile.file_path).name}"
            if progress_value_count is not None:
                if hasattr(progress_value_count, "set"):
                    progress_value_count.set(progress_value_count.get() + 1)
                else:
                    progress_value_count += 1
            if progress_callback_cmd is not None:
                progress_callback_cmd()

            # reset recipient data
            dico_layer = {}
            # getting the informations
            try:
                geofile.georeader().infos_dataset(
                    source_path=path.abspath(geofile.file_path),
                    dico_dataset=dico_layer,
                    txt=self.localized_strings,
                )
                logger.debug(f"Reading {geofile} succeeded.")
                geofile.processed = True
            except Exception as err:
                logger.error(
                    f"Reading and extraction information on file {geofile.file_path} "
                    f"(format: {geofile.file_format}) failed. Trace: {err}"
                )
                geofile.processed = True
                geofile.process_error = err
                continue

            # storing informations into the output file
            try:
                if progress_value_message is not None:
                    progress_value_message = f"Storing: {geofile.file_path}"
                # writing to the Excel file
                self.output_workbook.store_md_vector(layer=dico_layer)
                geofile.exported = True
                logger.debug(f"Metadata stored into workbook for {geofile.file_path}")
            except Exception as err:
                geofile.exported = False
                geofile.exported = err
                logger.error(
                    f"Storing metadata of {geofile.file_path} into the output file "
                    f"failed. Trace: {err}"
                )

    def add_files_to_process_queue(
        self, list_of_files: list, file_format: str
    ) -> list[FileToProcess]:
        out_list: list = []

        for geofile in list_of_files:
            out_list.append(
                FileToProcess(
                    file_path=geofile,
                    file_format=file_format,
                    georeader=self.MATRIX_FORMAT_GEOREADER.get(file_format),
                )
            )

        self.li_files_to_process.extend(out_list)
        logger.debug(
            f"{len(out_list)} files (format: {file_format}) added to the "
            "process queue."
        )
        return out_list

    def count_files_to_process(self) -> int:
        total_files: int = 0
        if self.opt_analyze_shapefiles and len(self.li_shapefiles):
            total_files += len(self.li_shapefiles)
            self.output_workbook.set_worksheets(has_vector=1)
            self.add_files_to_process_queue(
                list_of_files=self.li_shapefiles, file_format="esri_shapefile"
            )
        else:
            pass

        if self.opt_analyze_mapinfo_tab and len(self.li_mapinfo_tab):
            total_files += len(self.li_mapinfo_tab)
            self.output_workbook.set_worksheets(has_vector=1)
            self.add_files_to_process_queue(
                list_of_files=self.li_mapinfo_tab, file_format="mapinfo_tab"
            )
        else:
            pass

        if self.opt_analyze_kml and len(self.li_kml):
            total_files += len(self.li_kml)
            self.output_workbook.set_worksheets(has_vector=1)
            self.add_files_to_process_queue(
                list_of_files=self.li_kml, file_format="kml"
            )
        else:
            pass

        if self.opt_analyze_gml and len(self.li_gml):
            total_files += len(self.li_gml)
            self.output_workbook.set_worksheets(has_vector=1)
            self.add_files_to_process_queue(
                list_of_files=self.li_gml, file_format="gml"
            )
        else:
            pass

        if self.opt_analyze_geojson and len(self.li_geojson):
            total_files += len(self.li_geojson)
            self.output_workbook.set_worksheets(has_vector=1)
            self.add_files_to_process_queue(
                list_of_files=self.li_geojson, file_format="geojson"
            )
        else:
            pass

        if self.opt_analyze_gxt and len(self.li_gxt):
            total_files += len(self.li_gxt)
            self.output_workbook.set_worksheets(has_vector=1)
            self.add_files_to_process_queue(
                list_of_files=self.li_gxt, file_format="gxt"
            )
        else:
            pass

        if self.opt_analyze_raster and len(self.li_rasters):
            total_files += len(self.li_rasters)
            self.output_workbook.set_worksheets(has_raster=1)
            self.add_files_to_process_queue(
                list_of_files=self.li_tif, file_format="raster"
            )
        else:
            pass

        if self.opt_analyze_esri_filegdb and len(self.li_filegdb_esri):
            total_files += len(self.li_filegdb_esri)
            self.output_workbook.set_worksheets(has_filedb=1)
            self.add_files_to_process_queue(
                list_of_files=self.li_filegdb_esri, file_format="file_geodatabase_esri"
            )
        else:
            pass

        if self.opt_analyze_spatialite and len(self.li_filegdb_spatialite):
            total_files += len(self.li_filegdb_spatialite)
            self.output_workbook.set_worksheets(has_filedb=1)
            self.add_files_to_process_queue(
                list_of_files=self.li_filegdb_spatialite,
                file_format="file_geodatabase_spatialite",
            )
        else:
            pass

        if self.opt_analyze_cdao and len(self.li_cdao):
            total_files += len(self.li_cdao)
            self.output_workbook.set_worksheets(has_cad=1)
            self.add_files_to_process_queue(
                list_of_files=self.li_cdao, file_format="file_geodatabase_spatialite"
            )
        else:
            pass

        self.total_files = total_files
        return total_files
