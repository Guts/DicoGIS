#! python3  # noqa: E265


# ##############################################################################
# ########## Libraries #############
# ##################################

# standard library
import logging
from pathlib import Path
from typing import Optional

# package
from dicogis.utils.texts import TextsManager
from dicogis.utils.utils import Utilities

# ##############################################################################
# ############ Globals ############
# #################################

dir_locale = Path(__file__).parent / "locale"
txt_manager = TextsManager(dir_locale)
utils_global = Utilities()

# LOG
logger = logging.getLogger("DicoGIS")


# ##############################################################################
# ############ Functions ##########
# #################################


def process_files(
    output_workbook,
    # input lists of files to process
    li_gml: Optional[list],
    li_kml: Optional[list],
    li_mapinfo_tab: Optional[list],
    li_shapefiles: Optional[list],
    li_vectors: Optional[list],
    li_rasters: Optional[list],
    li_file_databases: Optional[list],
    li_cdao: Optional[list],
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
):
    # sheets and progress bar
    total_files: int = 0
    if opt_analyze_shapefiles and len(li_shapefiles):
        total_files += len(li_shapefiles)
        output_workbook.set_worksheets(has_vector=1)
    else:
        pass
    if opt_analyze_mapinfo_tab and len(li_mapinfo_tab):
        total_files += len(li_mapinfo_tab)
        output_workbook.set_worksheets(has_vector=1)
    else:
        pass
    # if .get() and len(self.li_kml):
    #     total_files += len(self.li_kml)
    #     output_workbook.set_worksheets(has_vector=1)
    # else:
    #     pass
    # if self.tab_files.opt_gml.get() and len(self.li_gml):
    #     total_files += len(self.li_gml)
    #     output_workbook.set_worksheets(has_vector=1)
    # else:
    #     pass
    # if self.tab_files.opt_geoj.get() and len(self.li_geoj):
    #     total_files += len(self.li_geoj)
    #     output_workbook.set_worksheets(has_vector=1)
    # else:
    #     pass
    # if self.tab_files.opt_gxt.get() and len(self.li_gxt):
    #     total_files += len(self.li_gxt)
    #     output_workbook.set_worksheets(has_vector=1)
    # else:
    #     pass
    # if self.tab_files.opt_rast.get() and len(self.li_raster):
    #     total_files += len(self.li_raster)
    #     output_workbook.set_worksheets(has_raster=1)
    # else:
    #     pass
    # if self.tab_files.opt_egdb.get() and len(self.li_egdb):
    #     total_files += len(self.li_egdb)
    #     output_workbook.set_worksheets(has_filedb=1)
    # else:
    #     pass
    # if self.tab_files.opt_spadb.get() and len(self.li_spadb):
    #     total_files += len(self.li_spadb)
    #     output_workbook.set_worksheets(has_filedb=1)
    # else:
    #     pass
    # if self.tab_files.opt_cdao.get() and len(self.li_cdao):
    #     total_files += len(self.li_cdao)
    #     output_workbook.set_worksheets(has_cad=1)
    # else:
    #     pass

    # self.prog_layers["maximum"] = total_files
    # self.prog_layers["value"]

    # if self.tab_files.opt_shp.get() and len(li_shapefiles) > 0:
    #     logger.info("Processing shapefiles: start")
    #     for shp in li_shapefiles:
    #         """looping on shapefiles list"""
    #         self.status.set(path.basename(shp))
    #         logger.info(f"Processing: {shp}")
    #         # increment the progress bar
    #         self.prog_layers["value"] = self.prog_layers["value"] + 1
    #         self.update()
    #         # reset recipient data
    #         self.dico_layer.clear()
    #         # getting the informations
    #         try:
    #             georeader_vector.infos_dataset(
    #                 path.abspath(shp), self.dico_layer, self.blabla
    #             )
    #             logger.debug("Dataset metadata extracted")
    #         except (AttributeError, RuntimeError, Exception) as err:
    #             """empty files"""
    #             logger.error(
    #                 "Metadata extraction failed on dataset: {}. Trace: {}".format(
    #                     shp, err
    #                 )
    #             )
    #             self.prog_layers["value"] = self.prog_layers["value"] + 1
    #             continue
    #         # writing to the Excel dictionary
    #         output_workbook.store_md_vector(self.dico_layer)

    #         logger.debug("Layer metadata stored into workbook.")
    # else:
    #     if len(li_shapefiles):
    #         logger.info(f"Ignoring {len(li_shapefiles)} shapefiles")
    #     pass

    # if self.tab_files.opt_tab.get() and len(li_mapinfo_tab) > 0:
    #     logger.info("Processing MapInfo tables: start")
    #     for tab in li_mapinfo_tab:
    #         """looping on MapInfo tables list"""
    #         self.status.set(path.basename(tab))
    #         logger.info(tab)
    #         # increment the progress bar
    #         self.prog_layers["value"] = self.prog_layers["value"] + 1
    #         self.update()
    #         # reset recipient data
    #         self.dico_layer.clear()
    #         # getting the informations
    #         try:
    #             georeader_vector.infos_dataset(
    #                 path.abspath(tab), self.dico_layer, self.blabla
    #             )
    #             logger.debug("Dataset metadata extracted")
    #         except (AttributeError, RuntimeError, Exception) as err:
    #             """empty files"""
    #             logger.error(
    #                 "Metadata extraction failed on dataset: {}. Trace: {}".format(
    #                     tab, err
    #                 )
    #             )
    #             self.prog_layers["value"] = self.prog_layers["value"] + 1
    #             continue
    #         # writing to the Excel file
    #         output_workbook.store_md_vector(self.dico_layer)

    #         logger.debug("Layer metadata stored into workbook.")
    # else:
    #     if len(li_mapinfo_tab):
    #         logger.info(f"Ignoring {len(li_mapinfo_tab)} MapInfo tables")

    # if .get() and len(self.li_kml) > 0:
    #     logger.info("Processing KML-KMZ: start")
    #     for kml in self.li_kml:
    #         """looping on KML/KMZ list"""
    #         self.status.set(path.basename(kml))
    #         logger.info(kml)
    #         # increment the progress bar
    #         self.prog_layers["value"] = self.prog_layers["value"] + 1
    #         self.update()
    #         # reset recipient data
    #         self.dico_layer.clear()
    #         self.dico_fields.clear()
    #         # getting the informations
    #         try:
    #             georeader_vector.infos_dataset(
    #                 path.abspath(kml), self.dico_layer, self.blabla
    #             )
    #             logger.debug("Dataset metadata extracted")
    #         except (AttributeError, RuntimeError, Exception) as err:
    #             """empty files"""
    #             logger.error(
    #                 "Metadata extraction failed on dataset: {}. Trace: {}".format(
    #                     kml, err
    #                 )
    #             )
    #             self.prog_layers["value"] = self.prog_layers["value"] + 1
    #             continue
    #         # writing to the Excel dictionary
    #         output_workbook.store_md_vector(self.dico_layer)
    #         logger.debug("Layer metadata stored into workbook.")
    # else:
    #     if len(self.li_kml):
    #         logger.info(f"Ignoring {len(self.li_kml)} KML")

    # if self.tab_files.opt_gml.get() and len(self.li_gml) > 0:
    #     logger.info("Processing GML: start")
    #     for gml in self.li_gml:
    #         """looping on GML list"""
    #         self.status.set(path.basename(gml))
    #         logger.info(gml)
    #         # increment the progress bar
    #         self.prog_layers["value"] = self.prog_layers["value"] + 1
    #         self.update()
    #         # reset recipient data
    #         self.dico_layer.clear()
    #         self.dico_fields.clear()
    #         # getting the informations
    #         try:
    #             georeader_vector.infos_dataset(
    #                 path.abspath(gml), self.dico_layer, self.blabla
    #             )
    #             logger.debug("Dataset metadata extracted")
    #         except (AttributeError, RuntimeError, Exception) as err:
    #             """empty files"""
    #             logger.error(
    #                 "Metadata extraction failed on dataset: {}. Trace: {}".format(
    #                     gml, err
    #                 )
    #             )
    #             self.prog_layers["value"] = self.prog_layers["value"] + 1
    #             continue
    #         # writing to the Excel dictionary
    #         output_workbook.store_md_vector(self.dico_layer)
    #         logger.debug("Layer metadata stored into workbook.")
    # else:
    #     if len(self.li_gml):
    #         logger.info(f"Ignoring {len(self.li_gml)} GML")

    # if self.tab_files.opt_geoj.get() and len(self.li_geoj) > 0:
    #     logger.info("Processing GeoJSON: start")
    #     for geojson in self.li_geoj:
    #         """looping on GeoJSON list"""
    #         self.status.set(path.basename(geojson))
    #         logger.info(geojson)
    #         # increment the progress bar
    #         self.prog_layers["value"] = self.prog_layers["value"] + 1
    #         self.update()
    #         # reset recipient data
    #         self.dico_layer.clear()
    #         self.dico_fields.clear()
    #         # getting the informations
    #         try:
    #             georeader_vector.infos_dataset(
    #                 path.abspath(geojson), self.dico_layer, self.blabla
    #             )
    #             logger.debug("Dataset metadata extracted")
    #         except (AttributeError, RuntimeError, Exception) as err:
    #             """empty files"""
    #             logger.error(
    #                 "Metadata extraction failed on dataset: {}. Trace: {}".format(
    #                     geojson, err
    #                 )
    #             )
    #             self.prog_layers["value"] = self.prog_layers["value"] + 1
    #             continue
    #         # writing to the Excel dictionary
    #         output_workbook.store_md_vector(self.dico_layer)
    #         logger.debug("Layer metadata stored into workbook.")
    # else:
    #     if len(self.li_geoj):
    #         logger.info(f"Ignoring {len(self.li_geoj)} GeoJSON")

    # if self.tab_files.opt_gxt.get() and len(self.li_gxt) > 0:
    #     logger.info("Processing GXT: start")
    #     for gxtpath in self.li_gxt:
    #         """looping on gxt list"""
    #         self.status.set(path.basename(gxtpath))
    #         logger.info(gxtpath)
    #         # increment the progress bar
    #         self.prog_layers["value"] = self.prog_layers["value"] + 1
    #         self.update()
    #         # reset recipient data
    #         self.dico_layer.clear()
    #         self.dico_fields.clear()
    #         # getting the informations
    #         try:
    #             ReadGXT(
    #                 path.abspath(gxtpath),
    #                 self.dico_layer,
    #                 "Geoconcept eXport Text",
    #                 self.blabla,
    #             )
    #             logger.debug("Dataset metadata extracted")
    #         except (AttributeError, RuntimeError, Exception) as err:
    #             """empty files"""
    #             logger.error(
    #                 "Metadata extraction failed on dataset: {}. Trace: {}".format(
    #                     gxtpath, err
    #                 )
    #             )
    #             self.prog_layers["value"] = self.prog_layers["value"] + 1
    #             continue
    #         # writing to the Excel dictionary
    #         output_workbook.store_md_vector(self.dico_layer)
    #         logger.debug("Layer metadata stored into workbook.")
    # else:
    #     if len(self.li_gxt):
    #         logger.info(f"Ignoring {len(self.li_gxt)} Geoconcept eXport Text")

    # if self.tab_files.opt_rast.get() and len(self.li_raster) > 0:
    #     logger.info("Processing rasters: start")
    #     for raster in self.li_raster:
    #         """looping on rasters list"""
    #         self.status.set(path.basename(raster))
    #         logger.info(raster)
    #         # increment the progress bar
    #         self.prog_layers["value"] = self.prog_layers["value"] + 1
    #         self.update()
    #         # reset recipient data
    #         self.dico_raster.clear()
    #         self.dico_bands.clear()
    #         # getting the informations
    #         try:
    #             ReadRasters(
    #                 path.abspath(raster),
    #                 self.dico_raster,
    #                 self.dico_bands,
    #                 path.splitext(raster)[1],
    #                 self.blabla,
    #             )
    #             logger.debug("Dataset metadata extracted")
    #         except (AttributeError, RuntimeError, Exception) as err:
    #             """empty files"""
    #             logger.error(
    #                 "Metadata extraction failed on dataset: {}. Trace: {}".format(
    #                     raster, err
    #                 )
    #             )
    #             self.prog_layers["value"] = self.prog_layers["value"] + 1
    #             continue
    #         # writing to the Excel dictionary
    #         output_workbook.store_md_raster(self.dico_raster, self.dico_bands)
    #         logger.debug("Layer metadata stored into workbook.")
    # else:
    #     if len(self.li_raster):
    #         logger.info(f"Ignoring {len(self.li_raster)} rasters")

    # if self.tab_files.opt_egdb.get() and len(self.li_egdb) > 0:
    #     logger.info("Processing Esri FileGDB: start")
    #     for gdb in self.li_egdb:
    #         """looping on FileGDB list"""
    #         self.status.set(path.basename(gdb))
    #         logger.info(gdb)
    #         # increment the progress bar
    #         self.prog_layers["value"] = self.prog_layers["value"] + 1
    #         self.update()
    #         # reset recipient data
    #         self.dico_fdb.clear()
    #         self.dico_fields.clear()
    #         # getting the informations
    #         try:
    #             georeader_egdb.infos_dataset(
    #                 path.abspath(gdb),
    #                 self.dico_fdb,
    #                 self.blabla,
    #                 tipo="Esri FileGDB",
    #             )
    #             logger.debug("Dataset metadata extracted")
    #         except (AttributeError, RuntimeError, Exception) as err:
    #             """empty files"""
    #             logger.error(
    #                 "Metadata extraction failed on dataset: {}. Trace: {}".format(
    #                     gdb, err
    #                 )
    #             )
    #             self.prog_layers["value"] = self.prog_layers["value"] + 1
    #             continue
    #         # writing to the Excel dictionary
    #         output_workbook.store_md_fdb(self.dico_fdb)
    #         logger.debug("Layer metadata stored into workbook.")
    # else:
    #     if len(self.li_egdb):
    #         logger.info(f"Ignoring {len(self.li_egdb)} Esri FileGDB")

    # if self.tab_files.opt_spadb.get() and len(self.li_spadb) > 0:
    #     logger.info("Processing Spatialite DB: start")
    #     for spadb in self.li_spadb:
    #         """looping on Spatialite DBs list"""
    #         self.status.set(path.basename(spadb))
    #         logger.info(spadb)
    #         # increment the progress bar
    #         self.prog_layers["value"] = self.prog_layers["value"] + 1
    #         self.update()
    #         # reset recipient data
    #         self.dico_fdb.clear()
    #         self.dico_fields.clear()
    #         # getting the informations
    #         try:
    #             ReadSpaDB(
    #                 path.abspath(spadb), self.dico_fdb, "Spatialite", self.blabla
    #             )
    #             logger.debug("Dataset metadata extracted")
    #         except (AttributeError, RuntimeError, Exception) as err:
    #             """empty files"""
    #             logger.error(
    #                 "Metadata extraction failed on dataset: {}. Trace: {}".format(
    #                     spadb, err
    #                 )
    #             )
    #             self.prog_layers["value"] = self.prog_layers["value"] + 1
    #             continue
    #         # writing to the Excel dictionary
    #         output_workbook.store_md_fdb(self.dico_fdb)
    #         logger.debug("Layer metadata stored into workbook.")
    # else:
    #     if len(self.li_spadb):
    #         logger.info(f"Ignoring {len(self.li_spadb)} Spatialite DB")

    # if self.tab_files.opt_cdao.get() and len(self.li_cdao) > 0:
    #     logger.info("Processing CAO/DAO: start")
    #     for dxf in self.li_dxf:
    #         """looping on DXF list"""
    #         self.status.set(path.basename(dxf))
    #         logger.info(dxf)
    #         # increment the progress bar
    #         self.prog_layers["value"] = self.prog_layers["value"] + 1
    #         self.update()
    #         # reset recipient data
    #         self.dico_cdao.clear()
    #         # getting the informations
    #         try:
    #             ReadDXF(
    #                 path.abspath(dxf), self.dico_cdao, "AutoCAD DXF", self.blabla
    #             )
    #             logger.debug("Dataset metadata extracted")
    #         except (AttributeError, RuntimeError, Exception) as err:
    #             """empty files"""
    #             logger.error(
    #                 "Metadata extraction failed on dataset: {}. Trace: {}".format(
    #                     dxf, err
    #                 )
    #             )
    #             self.prog_layers["value"] = self.prog_layers["value"] + 1
    #             continue
    #         # writing to the Excel dictionary
    #         output_workbook.store_md_cad(self.dico_cdao)
    #         logger.debug("Layer metadata stored into workbook.")
    # else:
    #     if len(self.li_cdao):
    #         logger.info(f"Ignoring {len(self.li_cdao)} CAO/DAO files")

    # # saving dictionary
    # self.bell()
    # self.val.config(state=ACTIVE)
    # output_workbook.tunning_worksheets()
    # saved = utils_global.safe_save(
    #     wb=output_workbook,
    #     dest_dir=self.tab_files.target_path.get(),
    #     dest_filename=self.ent_outxl_filename.get(),
    #     ftype="Excel Workbook",
    #     dlg_title=self.blabla.get("gui_excel"),
    # )
    # logger.info("Workbook saved: %s", self.ent_outxl_filename.get())

    # # quit and exit
    # if saved is not None:
    #     utils_global.open_dir_file(saved[1])
    # else:
    #     showinfo(
    #         title=self.blabla.get(
    #             "no_output_file_selected", "No output file selected"
    #         ),
    #         message=self.blabla.get(
    #             "no_output_file_selected", "Dictionary has not been saved."
    #         ),
    #     )
