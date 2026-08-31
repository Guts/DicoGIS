#! python3  # noqa: E265

"""
Look for geographic datasets.
"""

# #############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field, fields
from functools import partial as partial_func
from os import path, walk
from pathlib import Path

# 3rd party
import pgserviceparser

# package
from dicogis.constants import FormatsRaster
from dicogis.utils.progress import ProgressReporter, raise_if_canceled

# #############################################################################
# ########## Globals ###############
# ##################################

logger = logging.getLogger(__name__)

# extension -> bucket key, for formats identified by extension alone (no
# companion-file validation needed, unlike shapefiles/MapInfo TAB). Adding a
# new such format only means adding an entry here and to the `buckets` dict
# built alongside every _PartialListing. FormatsRaster.has_value() is checked
# as a fallback for any extension not listed here (currently .ecw, .jpeg).
EXTENSION_TO_BUCKET: dict[str, str] = {
    ".kml": "kml",
    ".kmz": "kml",
    ".gml": "gml",
    ".geojson": "geoj",
    ".geotiff": "geotiff",
    ".tif": "geotiff",
    ".tiff": "geotiff",
    ".gxt": "gxt",
    ".dxf": "dxf",
    ".dwg": "dwg",
    ".dgn": "dgn",
    ".gpkg": "geopackage",
    ".sqlite": "spatialite",
}


# #############################################################################
# ########## Classes ###############
# ##################################


@dataclass
class _PartialListing:
    """Geodata files found under one directory (sub)tree, before the final
    sort/grouping pass done by find_geodata_files(). Each worker thread and
    the top level of the walk get their own instance, merged afterwards -
    this is what lets the scan be parallelized without any locking."""

    num_folders: int = 0
    shp: list[str] = field(default_factory=list)
    tab: list[str] = field(default_factory=list)
    kml: list[str] = field(default_factory=list)
    gml: list[str] = field(default_factory=list)
    geoj: list[str] = field(default_factory=list)
    geotiff: list[str] = field(default_factory=list)
    gxt: list[str] = field(default_factory=list)
    dxf: list[str] = field(default_factory=list)
    dwg: list[str] = field(default_factory=list)
    dgn: list[str] = field(default_factory=list)
    geopackage: list[str] = field(default_factory=list)
    spatialite: list[str] = field(default_factory=list)
    filegdb: list[str] = field(default_factory=list)
    raster: list[str] = field(default_factory=list)

    def buckets(self) -> dict[str, list[str]]:
        """Bucket key (see EXTENSION_TO_BUCKET) -> list to append matches
        into. Excludes shp/tab/raster/filegdb, which need extra logic beyond
        a plain extension lookup and are handled separately."""
        return {
            "kml": self.kml,
            "gml": self.gml,
            "geoj": self.geoj,
            "geotiff": self.geotiff,
            "gxt": self.gxt,
            "dxf": self.dxf,
            "dwg": self.dwg,
            "dgn": self.dgn,
            "geopackage": self.geopackage,
            "spatialite": self.spatialite,
        }


# ##############################################################################
# ########## Functions #############
# ##################################


def check_usable_pg_services(requested_pg_services: list[str]) -> list[str] | None:
    """Check if specified postgres services are actually referenced into the
        pg_service.conf. Filters out services which are not present.

    Args:
        requested_pg_services (list[str]): list of requested services names

    Returns:
        list[str]: filtered list of services names
    """
    out_pg_srv_list: list[str] = []
    referenced_srv = pgserviceparser.service_names()

    for in_pg_srv in requested_pg_services:
        if in_pg_srv not in referenced_srv:
            logger.warning(
                f"{in_pg_srv} is not among Posgtres services referenced within "
                f"{pgserviceparser.conf_path()}: {', '.join(referenced_srv)}"
            )
            continue

        out_pg_srv_list.append(in_pg_srv)

    return out_pg_srv_list


def _process_one_walk_level(
    root: str,
    dirs: list[str],
    files: list[str],
    result: _PartialListing,
    buckets: dict[str, list[str]],
) -> list[str]:
    """Classify one os.walk() level's dirs/files into `result`.

    Args:
        root: directory these dirs/files belong to (as yielded by os.walk()).
        dirs: subdirectories of root, as yielded by os.walk().
        files: files directly in root, as yielded by os.walk().
        result: partial listing to fill in place.
        buckets: result.buckets(), passed in rather than recomputed so
            callers can build it once per tree instead of once per level.

    Returns:
        The subset of `dirs` that should still be descended into, i.e. with
        detected FileGeoDatabases pruned out: they're captured as a single
        dataset here and can otherwise contain thousands of internal files
        that would be inspected for nothing.
    """
    result.num_folders += len(dirs)
    gdb_dirs: list[str] = []
    for d in dirs:
        """looking for File Geodatabase among directories"""
        full_path = path.join(root, d)
        if full_path[-4:].lower() == ".gdb":
            # add complete path of Esri FileGeoDatabase
            result.filegdb.append(path.abspath(full_path))
            gdb_dirs.append(d)
    pruned_dirs = [d for d in dirs if d not in gdb_dirs] if gdb_dirs else dirs

    # lowercased filenames of this directory, built once: lets shapefile/
    # MapInfo companion checks below be plain set membership tests instead of
    # one isfile() stat() round-trip per case variant. This also makes the
    # check tolerant to companions whose extension case differs from the main
    # file's, e.g. "cities.shp" + "cities.DBF" (still seen in older/legacy
    # GIS exports), which touching the disk per case variant already tried
    # to cover.
    files_lower: set[str] = {name.lower() for name in files}
    for f in files:
        """looking for files with geographic data"""
        full_path = path.join(root, f)
        f_stem_lower, f_ext_lower = path.splitext(f.lower())
        if (
            f_ext_lower == ".shp"
            and f"{f_stem_lower}.dbf" in files_lower
            and f"{f_stem_lower}.shx" in files_lower
        ):
            """listing compatible shapefiles"""
            # add complete path of shapefile
            result.shp.append(full_path)
        elif (
            f_ext_lower == ".tab"
            and f"{f_stem_lower}.dat" in files_lower
            and f"{f_stem_lower}.map" in files_lower
            and f"{f_stem_lower}.id" in files_lower
        ):
            """listing MapInfo tables"""
            result.tab.append(full_path)
        elif bucket_key := EXTENSION_TO_BUCKET.get(f_ext_lower):
            buckets[bucket_key].append(full_path)
        elif FormatsRaster.has_value(f_ext_lower):
            """listing compatible rasters"""
            result.raster.append(full_path)

    return pruned_dirs


def _scan_directory_tree(
    root: str, progress_reporter: ProgressReporter | None = None
) -> _PartialListing:
    """Recursively scan one directory tree into its own partial result.

    Runs standalone - its own os.walk(), no shared mutable state - so it can
    safely be handed to a worker thread by find_geodata_files(). Only reads
    from `progress_reporter` (is_canceled()), never writes progress to it:
    when running in a worker thread, reporting is left to the main thread
    merging the results, so implementations don't need a thread-safe counter.

    Raises:
        OperationCanceled: if the progress reporter asked to stop. Raised
            from the worker thread, and re-raised in the calling thread by
            the executor when the result is consumed.
    """
    result = _PartialListing()
    buckets = result.buckets()
    for current_root, dirs, files in walk(root):
        raise_if_canceled(progress_reporter)
        dirs[:] = _process_one_walk_level(current_root, dirs, files, result, buckets)
    return result


def _merge_partial(into: _PartialListing, other: _PartialListing) -> None:
    """Fold `other`'s matches into `into`, in place."""
    into.num_folders += other.num_folders
    for a_field in fields(_PartialListing):
        if a_field.name == "num_folders":
            continue
        getattr(into, a_field.name).extend(getattr(other, a_field.name))


def find_geodata_files(
    start_folder: Path,
    parallel_scan: bool = False,
    max_workers: int | None = None,
    progress_reporter: ProgressReporter | None = None,
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
    list[str],
    list[str],
]:
    """List compatible geo-files stored into a folder structure.

    Args:
        start_folder (Path): folder to start.
        parallel_scan (bool): scan top-level subfolders in parallel worker
            threads (each recursing through its own branch independently)
            instead of a single sequential walk. Off by default: benchmarks
            show this is a net loss on local/fast storage (the per-file
            classification work is CPU-bound Python, so threads mostly
            fight over the GIL instead of overlapping I/O) and only pays
            off on high-latency storage such as network-mounted shares,
            with a tree deep enough to have many directories to overlap.
            Only enable it when scanning a known-slow/network location.
        max_workers (int | None): passed to ThreadPoolExecutor when
            parallel_scan is True; ignored otherwise. Defaults to
            ThreadPoolExecutor's own default (based on CPU count).
        progress_reporter (ProgressReporter | None): reporter notified of
            folders as they're scanned, and polled for cancellation. None
            (the default, and what dicogis-cli passes) disables both.
            Note that set_total() is never called: the number of folders
            can't be known before walking the tree, so this stage reports a
            running count and the folder being scanned, not a percentage.

    Returns:
        tuple[ int, list[str], list[str], list[str], list[str], list[str], list[str],
        list[str], list[str], list[str], list[str], list[str], list[str], list[str],
        list[str], ]: tuple with number of folders parsed and list of paths by formats

    Raises:
        OperationCanceled: if the progress reporter asked to stop. Nothing is
            returned in that case: a partial listing is indistinguishable from
            a complete one for callers downstream.
    """
    logger.info(f"Begin of folders parsing: {start_folder}")
    root_str = str(start_folder)

    result = _PartialListing()
    buckets = result.buckets()

    already_reported = 0

    def _report_scanned(folders_done: int, current_folder: str) -> None:
        """Report scan advancement, from the calling thread only."""
        nonlocal already_reported
        if progress_reporter is None:
            return
        progress_reporter.set_message(f"Scanning ({folders_done}): {current_folder}")
        progress_reporter.increment(amount=folders_done - already_reported)
        already_reported = folders_done

    if not parallel_scan:
        for current_root, dirs, files in walk(root_str):
            raise_if_canceled(progress_reporter)
            dirs[:] = _process_one_walk_level(
                current_root, dirs, files, result, buckets
            )
            _report_scanned(result.num_folders, current_root)
    else:
        top_root, top_dirs, top_files = next(walk(root_str), (root_str, [], []))
        pruned_dirs = _process_one_walk_level(
            top_root, top_dirs, top_files, result, buckets
        )
        _report_scanned(result.num_folders, top_root)
        if pruned_dirs:
            subtree_roots = [path.join(top_root, d) for d in pruned_dirs]
            scan_subtree = partial_func(
                _scan_directory_tree, progress_reporter=progress_reporter
            )
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # worker threads only poll is_canceled(); progress is reported
                # here, in the calling thread, as each subtree comes back - so
                # a ProgressReporter never needs a thread-safe counter.
                for subtree_root, subtree in zip(
                    subtree_roots, executor.map(scan_subtree, subtree_roots)
                ):
                    _merge_partial(result, subtree)
                    _report_scanned(result.num_folders, subtree_root)

    # grouping raster
    li_raster = result.raster
    li_raster.extend(result.geotiff)

    # grouping CAO/DAO files
    li_cdao: list[str] = []
    li_cdao.extend(result.dxf)
    li_cdao.extend(result.dwg)
    li_cdao.extend(result.dgn)
    # grouping File geodatabases
    li_fdb: list[str] = []
    li_fdb.extend(result.filegdb)
    li_fdb.extend(result.spatialite)
    li_fdb.extend(result.geopackage)

    logger.info(
        f"End of folders parsing: {len(result.shp)} shapefiles - "
        f"{len(result.tab)} tables (MapInfo) - "
        f"{len(result.kml)} KML - "
        f"{len(result.gml)} GML - "
        f"{len(result.geoj)} GeoJSON"
        f"{len(li_raster)} rasters - "
        f"{len(result.filegdb)} Esri FileGDB - "
        f"{len(result.geopackage)} Geopackages - "
        f"{len(result.spatialite)} Spatialite - "
        f"{len(li_cdao)} CAO/DAO - "
        f"{len(result.gxt)} GXT - in {result.num_folders} folders"
    )

    # Lists ordering and tupling
    li_shp = tuple(sorted(result.shp))
    li_tab = tuple(sorted(result.tab))
    li_raster = sorted(li_raster)
    li_kml = tuple(sorted(result.kml))
    li_gml = tuple(sorted(result.gml))
    li_geoj = tuple(sorted(result.geoj))
    li_geotiff = sorted(result.geotiff)
    li_gxt = tuple(sorted(result.gxt))
    li_flat_geodatabases_esri_filegdb = tuple(sorted(result.filegdb))
    li_flat_geodatabases_geopackage = tuple(sorted(result.geopackage))
    li_flat_geodatabases_spatialite = tuple(sorted(result.spatialite))
    li_fdb = tuple(sorted(li_fdb))
    li_dxf = tuple(sorted(result.dxf))
    li_dwg = tuple(sorted(result.dwg))
    li_dgn = tuple(sorted(result.dgn))
    li_cdao = tuple(sorted(li_cdao))

    # End of function
    return (
        result.num_folders,
        li_shp,
        li_tab,
        li_kml,
        li_gml,
        li_geoj,
        li_geotiff,
        li_gxt,
        li_raster,
        li_flat_geodatabases_esri_filegdb,
        li_dxf,
        li_dwg,
        li_dgn,
        li_cdao,
        li_fdb,
        li_flat_geodatabases_spatialite,
        li_flat_geodatabases_geopackage,
    )
