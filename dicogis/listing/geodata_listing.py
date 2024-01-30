#! python3  # noqa: E265

"""
    Look for geographic datasets.
"""

# #############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import logging
from os import path, walk
from pathlib import Path

# package
from dicogis.constants import FormatsRaster

# #############################################################################
# ########## Globals ###############
# ##################################

logger = logging.getLogger(__name__)


# ##############################################################################
# ########## Functions #############
# ##################################


def find_geodata_files(
    start_folder: Path,
) -> tuple[
    int,
    list[str],
    list[str],
    list[str],
    list[str],
    list[str],
    list[str],
    list[str],
    list[str],
    list[str],
    list[str],
    list[str],
    list[str],
    list[str],
    list[str],
]:
    """List compatible geo-files stored into a folder structure.

    Args:
        start_folder (Path): folder to start.

    Returns:
        tuple[ int, list[str], list[str], list[str], list[str], list[str], list[str],
        list[str], list[str], list[str], list[str], list[str], list[str], list[str],
        list[str], ]: tuple with number of folders parsed and list of paths by formats
    """
    # counter
    num_folders: int = 0
    # final list by formats
    li_shp: list[str] = []
    li_tab: list[str] = []
    li_kml: list[str] = []
    li_gml: list[str] = []
    li_geoj: list[str] = []
    li_gxt: list[str] = []
    li_vectors: list[str] = []
    li_dxf: list[str] = []
    li_dwg: list[str] = []
    li_dgn: list[str] = []
    li_cdao: list[str] = []
    li_raster: list[str] = []
    li_fdb: list[str] = []
    li_egdb: list[str] = []
    li_spadb: list[str] = []

    # Looping in folders structure
    logger.info(f"Begin of folders parsing: {start_folder}")
    for root, dirs, files in walk(start_folder):
        num_folders = num_folders + len(dirs)
        for d in dirs:
            """looking for File Geodatabase among directories"""
            try:
                path.join(root, d)
                full_path = path.join(root, d)
            except UnicodeDecodeError:
                full_path = path.join(root, d.decode("latin1"))
            if full_path[-4:].lower() == ".gdb":
                # add complete path of Esri FileGeoDatabase
                li_egdb.append(path.abspath(full_path))
            else:
                pass
        for f in files:
            """looking for files with geographic data"""
            try:
                path.join(root, f)
                full_path = path.join(root, f)
            except UnicodeDecodeError:
                full_path = path.join(root, f.decode("latin1"))
            # Looping on files contained
            if (
                path.splitext(full_path.lower())[1].lower() == ".shp"
                and (
                    path.isfile(f"{full_path[:-4]}.dbf")
                    or path.isfile(f"{full_path[:-4]}.DBF")
                )
                and (
                    path.isfile(f"{full_path[:-4]}.shx")
                    or path.isfile(f"{full_path[:-4]}.SHX")
                )
            ):
                """listing compatible shapefiles"""
                # add complete path of shapefile
                li_shp.append(full_path)
            elif (
                path.splitext(full_path.lower())[1] == ".tab"
                and (
                    path.isfile(full_path[:-4] + ".dat")
                    or path.isfile(full_path[:-4] + ".DAT")
                )
                and (
                    path.isfile(full_path[:-4] + ".map")
                    or path.isfile(full_path[:-4] + ".MAP")
                )
                and (
                    path.isfile(full_path[:-4] + ".id")
                    or path.isfile(full_path[:-4] + ".ID")
                )
            ):
                """listing MapInfo tables"""
                # add complete path of MapInfo file
                li_tab.append(full_path)
            elif (
                path.splitext(full_path.lower())[1] == ".kml"
                or path.splitext(full_path.lower())[1] == ".kmz"
            ):
                """listing KML and KMZ"""
                # add complete path of KML file
                li_kml.append(full_path)
            elif path.splitext(full_path.lower())[1] == ".gml":
                """listing GML"""
                # add complete path of GML file
                li_gml.append(full_path)
            elif path.splitext(full_path.lower())[1] == ".geojson":
                """listing GeoJSON"""
                # add complete path of GeoJSON file
                li_geoj.append(full_path)
            elif path.splitext(full_path.lower())[1] == ".gxt":
                """listing Geoconcept eXport Text (GXT)"""
                # add complete path of GXT file
                li_gxt.append(full_path)
            elif FormatsRaster.has_key(path.splitext(full_path.lower())[1]):
                """listing compatible rasters"""
                # add complete path of raster file
                li_raster.append(full_path)
            elif path.splitext(full_path.lower())[1] == ".dxf":
                """listing DXF"""
                # add complete path of DXF file
                li_dxf.append(full_path)
            elif path.splitext(full_path.lower())[1] == ".dwg":
                """listing DWG"""
                # add complete path of DWG file
                li_dwg.append(full_path)
            elif path.splitext(full_path.lower())[1] == ".dgn":
                """listing MicroStation DGN"""
                # add complete path of DGN file
                li_dgn.append(full_path)
            elif path.splitext(full_path.lower())[1] == ".sqlite":
                """listing Spatialite DB"""
                # add complete path of DGN file
                li_spadb.append(full_path)
            else:
                continue

    # grouping CAO/DAO files
    li_cdao.extend(li_dxf)
    li_cdao.extend(li_dwg)
    li_cdao.extend(li_dgn)
    # grouping File geodatabases
    li_fdb.extend(li_egdb)
    li_fdb.extend(li_spadb)

    logger.info(
        f"End of folders parsing: {len(li_shp)} shapefiles - "
        f"{len(li_tab)} tables (MapInfo) - "
        f"{len(li_kml)} KML - "
        f"{len(li_gml)} GML - "
        f"{len(li_geoj)} GeoJSON"
        f"{len(li_raster)} rasters - "
        f"{len(li_egdb)} Esri FileGDB - "
        f"{len(li_spadb)} Spatialite - "
        f"{len(li_cdao)} CAO/DAO - "
        f"{len(li_gxt)} GXT - in {num_folders} folders"
    )

    # Lists ordering and tupling
    li_shp = tuple(sorted(li_shp))
    li_tab = tuple(sorted(li_tab))
    li_raster = tuple(sorted(li_raster))
    li_kml = tuple(sorted(li_kml))
    li_gml = tuple(sorted(li_gml))
    li_geoj = tuple(sorted(li_geoj))
    li_gxt = tuple(sorted(li_gxt))
    li_egdb = tuple(sorted(li_egdb))
    li_spadb = tuple(sorted(li_spadb))
    li_fdb = tuple(sorted(li_fdb))
    li_dxf = tuple(sorted(li_dxf))
    li_dwg = tuple(sorted(li_dwg))
    li_dgn = tuple(sorted(li_dgn))
    li_cdao = tuple(sorted(li_cdao))

    # End of function
    return (
        num_folders,
        li_shp,
        li_tab,
        li_kml,
        li_gml,
        li_geoj,
        li_gxt,
        li_raster,
        li_egdb,
        li_dxf,
        li_dwg,
        li_dgn,
        li_cdao,
        li_fdb,
        li_spadb,
    )
