#! python3  # noqa E265

"""
Usage from the repo root folder:

.. code-block:: bash
    # for whole tests
    python -m unittest tests.test_geodata_listing
    # for specific test
    python -m unittest tests.test_geodata_listing.TestFindGeodataFiles.test_shapefile_complete_is_detected
"""

# standard library
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# project
from dicogis.listing.geodata_listing import check_usable_pg_services, find_geodata_files
from dicogis.utils.progress import OperationCanceled


# ############################################################################
# ########## Globals #############
# ################################

# names of the values returned - in order - by find_geodata_files()
FIND_GEODATA_FILES_FIELDS = (
    "num_folders",
    "shp",
    "tab",
    "kml",
    "gml",
    "geojson",
    "geotiff",
    "gxt",
    "raster",
    "filegdb",
    "dxf",
    "dwg",
    "dgn",
    "cdao",
    "fdb",
    "spatialite",
    "geopackage",
)


def _find_geodata_files(start_folder: Path, parallel_scan: bool = False) -> dict:
    """Run find_geodata_files and return its tuple as a readable dict."""
    return dict(
        zip(
            FIND_GEODATA_FILES_FIELDS,
            find_geodata_files(start_folder, parallel_scan=parallel_scan),
            strict=False,
        )
    )


# ############################################################################
# ########## Classes #############
# ################################


class TestCheckUsablePgServices(unittest.TestCase):
    """Test filtering of requested pg_service names against pg_service.conf."""

    @patch("dicogis.listing.geodata_listing.pgserviceparser.conf_path")
    @patch("dicogis.listing.geodata_listing.pgserviceparser.service_names")
    def test_filters_out_unreferenced_services(
        self, mock_service_names, mock_conf_path
    ):
        """A requested service absent from pg_service.conf is dropped."""
        mock_service_names.return_value = ["srv_ok", "srv_other"]
        mock_conf_path.return_value = Path("/fake/pg_service.conf")

        result = check_usable_pg_services(["srv_ok", "srv_missing"])

        self.assertEqual(result, ["srv_ok"])

    @patch("dicogis.listing.geodata_listing.pgserviceparser.conf_path")
    @patch("dicogis.listing.geodata_listing.pgserviceparser.service_names")
    def test_keeps_all_referenced_services(self, mock_service_names, mock_conf_path):
        """Every requested service that is referenced is kept, in order."""
        mock_service_names.return_value = ["srv_a", "srv_b", "srv_c"]
        mock_conf_path.return_value = Path("/fake/pg_service.conf")

        result = check_usable_pg_services(["srv_c", "srv_a"])

        self.assertEqual(result, ["srv_c", "srv_a"])

    @patch("dicogis.listing.geodata_listing.pgserviceparser.conf_path")
    @patch("dicogis.listing.geodata_listing.pgserviceparser.service_names")
    def test_empty_request_returns_empty_list(self, mock_service_names, mock_conf_path):
        """No requested services means nothing to filter."""
        mock_service_names.return_value = ["srv_a"]
        mock_conf_path.return_value = Path("/fake/pg_service.conf")

        self.assertEqual(check_usable_pg_services([]), [])

    @patch("dicogis.listing.geodata_listing.pgserviceparser.conf_path")
    @patch("dicogis.listing.geodata_listing.pgserviceparser.service_names")
    def test_no_referenced_services_drops_everything(
        self, mock_service_names, mock_conf_path
    ):
        """If pg_service.conf has no services, all requests are dropped."""
        mock_service_names.return_value = []
        mock_conf_path.return_value = Path("/fake/pg_service.conf")

        self.assertEqual(check_usable_pg_services(["srv_a", "srv_b"]), [])


class _RecordingReporter:
    """Minimal ProgressReporter implementation recording what it's told.

    Deliberately not a Mock: it also asserts the listing stage never calls
    set_total(), since the folder count can't be known before walking.
    """

    def __init__(self, canceled: bool = False):
        self.messages: list[str] = []
        self.count = 0
        self.canceled = canceled
        self.set_total_calls = 0

    def set_message(self, message: str) -> None:
        self.messages.append(message)

    def increment(self, amount: int = 1) -> None:
        self.count += amount

    def set_total(self, total: int) -> None:
        self.set_total_calls += 1

    def is_canceled(self) -> bool:
        return self.canceled


class TestFindGeodataFilesProgressAndCancellation(unittest.TestCase):
    """Test the ProgressReporter plumbing of find_geodata_files()."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory(
            prefix="DicoGIS_test_listing_progress_", ignore_cleanup_errors=True
        )
        self.start_folder = Path(self.tmp_dir.name)
        for theme in ("cadastre", "voirie", "hydrographie"):
            leaf = self.start_folder / theme / "commune"
            leaf.mkdir(parents=True)
            (leaf / f"{theme}.gml").touch()

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_sequential_scan_reports_every_folder(self):
        """Increments add up to the folder count actually returned."""
        reporter = _RecordingReporter()

        result = find_geodata_files(self.start_folder, progress_reporter=reporter)

        self.assertEqual(reporter.count, result[0])
        self.assertTrue(reporter.messages)

    def test_parallel_scan_reports_every_folder(self):
        """Same total in parallel mode, even though progress is reported per
        finished subtree rather than per folder."""
        reporter = _RecordingReporter()

        result = find_geodata_files(
            self.start_folder, parallel_scan=True, progress_reporter=reporter
        )

        self.assertEqual(reporter.count, result[0])

    def test_set_total_is_never_called(self):
        """The listing stage has no knowable total, so it must not pretend to
        report a percentage."""
        reporter = _RecordingReporter()

        find_geodata_files(self.start_folder, progress_reporter=reporter)

        self.assertEqual(reporter.set_total_calls, 0)

    def test_sequential_scan_is_canceled(self):
        """A reporter asking to stop aborts the walk with OperationCanceled
        rather than returning a partial listing indistinguishable from a
        complete one."""
        reporter = _RecordingReporter(canceled=True)

        with self.assertRaises(OperationCanceled):
            find_geodata_files(self.start_folder, progress_reporter=reporter)

    def test_parallel_scan_is_canceled(self):
        """Cancellation raised inside a worker thread is re-raised in the
        calling thread by the executor."""
        reporter = _RecordingReporter(canceled=True)

        with self.assertRaises(OperationCanceled):
            find_geodata_files(
                self.start_folder, parallel_scan=True, progress_reporter=reporter
            )

    def test_no_reporter_never_cancels(self):
        """dicogis-cli passes None: the scan must run to completion."""
        result = find_geodata_files(self.start_folder, progress_reporter=None)

        self.assertEqual(result[0], 6)  # 3 themes + 3 commune subfolders


class TestFindGeodataFiles(unittest.TestCase):
    """Test folder-tree scanning and bucketing of geodata files by format."""

    def setUp(self):
        """Executed before each test."""
        self.tmp_dir = tempfile.TemporaryDirectory(
            prefix="DicoGIS_test_geodata_listing_", ignore_cleanup_errors=True
        )
        self.start_folder = Path(self.tmp_dir.name)

    def tearDown(self):
        """Executed after each test."""
        self.tmp_dir.cleanup()

    def _touch(self, *relative_parts: str) -> Path:
        """Create an empty file (and parent folders) under the temp folder."""
        file_path = self.start_folder.joinpath(*relative_parts)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.touch()
        return file_path

    # -- empty / irrelevant content ------------------------------------------

    # geotiff/raster are the two fields that stay plain lists (not tupled)
    # in find_geodata_files(), unlike every other bucket.
    LIST_TYPED_FIELDS = ("geotiff", "raster")

    def _assert_all_buckets_empty(self, result: dict) -> None:
        for field in FIND_GEODATA_FILES_FIELDS:
            if field == "num_folders":
                continue
            expected = [] if field in self.LIST_TYPED_FIELDS else ()
            self.assertEqual(result[field], expected, field)

    def test_empty_folder_returns_all_empty(self):
        """An empty folder yields zero folders and no files in any bucket."""
        result = _find_geodata_files(self.start_folder)

        self.assertEqual(result["num_folders"], 0)
        self._assert_all_buckets_empty(result)

    def test_unsupported_extension_is_ignored(self):
        """A file with an unrelated extension ends up in no bucket at all."""
        self._touch("readme.txt")

        result = _find_geodata_files(self.start_folder)

        self._assert_all_buckets_empty(result)

    def test_num_folders_counts_subdirectories(self):
        """num_folders counts every subdirectory encountered while walking."""
        self._touch("sub_a", "placeholder.txt")
        self._touch("sub_b", "nested", "placeholder.txt")

        result = _find_geodata_files(self.start_folder)

        # sub_a, sub_b and sub_b/nested
        self.assertEqual(result["num_folders"], 3)

    def test_files_across_multiple_top_level_folders_are_all_found(self):
        """With parallel_scan=True, top-level subfolders are scanned as
        independent units in worker threads: matches from every branch must
        still all end up merged in the result, whichever branch finishes
        first. Off by default (see find_geodata_files' docstring), so this
        is the one test that opts in to exercise that code path."""
        cadastre = self._touch("cadastre", "parcelle.shp")
        self._touch("cadastre", "parcelle.dbf")
        self._touch("cadastre", "parcelle.shx")
        voirie = self._touch("voirie", "route.geojson")
        hydro = self._touch("hydrographie", "riviere.gml")
        gdb_dir = self.start_folder / "batiments" / "data.gdb"
        gdb_dir.mkdir(parents=True)

        result = _find_geodata_files(self.start_folder, parallel_scan=True)

        self.assertEqual(result["shp"], (str(cadastre),))
        self.assertEqual(result["geojson"], (str(voirie),))
        self.assertEqual(result["gml"], (str(hydro),))
        self.assertEqual(result["filegdb"], (str(gdb_dir),))
        # cadastre, voirie, hydrographie, batiments, batiments/data.gdb
        self.assertEqual(result["num_folders"], 5)

    # -- shapefiles -----------------------------------------------------------

    def test_shapefile_complete_is_detected(self):
        """A .shp with its .dbf and .shx companions is listed."""
        shp = self._touch("cities.shp")
        self._touch("cities.dbf")
        self._touch("cities.shx")

        result = _find_geodata_files(self.start_folder)

        self.assertEqual(result["shp"], (str(shp),))

    def test_shapefile_missing_companion_is_ignored(self):
        """A .shp without its .dbf/.shx companions is not usable and dropped."""
        self._touch("cities.shp")
        self._touch("cities.dbf")
        # no .shx

        result = _find_geodata_files(self.start_folder)

        self.assertEqual(result["shp"], ())

    def test_shapefile_uppercase_companions_are_detected(self):
        """Legacy/DOS-era shapefile exports with uppercased companion
        extensions (.DBF/.SHX) are still recognized as complete."""
        shp = self._touch("cities.shp")
        self._touch("cities.DBF")
        self._touch("cities.SHX")

        result = _find_geodata_files(self.start_folder)

        self.assertEqual(result["shp"], (str(shp),))

    # -- MapInfo TAB ------------------------------------------------------------

    def test_mapinfo_tab_complete_is_detected(self):
        """A .tab with its .dat/.map/.id companions is listed."""
        tab = self._touch("parcels.tab")
        self._touch("parcels.dat")
        self._touch("parcels.map")
        self._touch("parcels.id")

        result = _find_geodata_files(self.start_folder)

        self.assertEqual(result["tab"], (str(tab),))

    def test_mapinfo_tab_missing_companion_is_ignored(self):
        """A .tab missing one of its required companions is dropped."""
        self._touch("parcels.tab")
        self._touch("parcels.dat")
        self._touch("parcels.map")
        # no .id

        result = _find_geodata_files(self.start_folder)

        self.assertEqual(result["tab"], ())

    def test_mapinfo_tab_uppercase_companions_are_detected(self):
        """Legacy MapInfo exports with uppercased companion extensions
        (.DAT/.MAP/.ID) are still recognized as complete."""
        tab = self._touch("parcels.tab")
        self._touch("parcels.DAT")
        self._touch("parcels.MAP")
        self._touch("parcels.ID")

        result = _find_geodata_files(self.start_folder)

        self.assertEqual(result["tab"], (str(tab),))

    # -- single-file formats ----------------------------------------------------

    def test_kml_and_kmz_are_detected(self):
        """Both .kml and .kmz are bucketed together as KML."""
        kml = self._touch("trail.kml")
        kmz = self._touch("trail.kmz")

        result = _find_geodata_files(self.start_folder)

        self.assertEqual(set(result["kml"]), {str(kml), str(kmz)})

    def test_gml_is_detected(self):
        """A .gml file is listed."""
        gml = self._touch("network.gml")

        result = _find_geodata_files(self.start_folder)

        self.assertEqual(result["gml"], (str(gml),))

    def test_geojson_is_detected(self):
        """A .geojson file is listed."""
        geojson = self._touch("districts.geojson")

        result = _find_geodata_files(self.start_folder)

        self.assertEqual(result["geojson"], (str(geojson),))

    def test_gxt_is_detected(self):
        """A .gxt (Geoconcept eXport Text) file is listed."""
        gxt = self._touch("survey.gxt")

        result = _find_geodata_files(self.start_folder)

        self.assertEqual(result["gxt"], (str(gxt),))

    # -- CAD / DAO formats --------------------------------------------------

    def test_cad_formats_are_grouped_into_cdao(self):
        """DXF, DWG and DGN each get their own bucket and are merged into cdao."""
        dxf = self._touch("plan.dxf")
        dwg = self._touch("plan.dwg")
        dgn = self._touch("plan.dgn")

        result = _find_geodata_files(self.start_folder)

        self.assertEqual(result["dxf"], (str(dxf),))
        self.assertEqual(result["dwg"], (str(dwg),))
        self.assertEqual(result["dgn"], (str(dgn),))
        self.assertEqual(set(result["cdao"]), {str(dxf), str(dwg), str(dgn)})

    # -- file geodatabases ----------------------------------------------------

    def test_esri_filegdb_directory_is_detected(self):
        """A directory ending in .gdb is treated as an Esri FileGeodatabase."""
        gdb_dir = self.start_folder / "data.gdb"
        gdb_dir.mkdir()

        result = _find_geodata_files(self.start_folder)

        # production code normalizes with os.path.abspath(), not Path.resolve() -
        # the latter also expands Windows 8.3 short names (e.g. RUNNER~1), which
        # would make this comparison fail on GitHub Actions Windows runners.
        self.assertEqual(result["filegdb"], (str(gdb_dir),))
        self.assertIn(str(gdb_dir), result["fdb"])

    def test_gdb_internals_are_not_traversed(self):
        """The walk does not descend into a detected .gdb: its internal files
        and subfolders don't inflate num_folders or leak into other buckets."""
        gdb_dir = self.start_folder / "data.gdb"
        gdb_dir.mkdir()
        (gdb_dir / "inner_subdir").mkdir()
        self._touch("data.gdb", "leftover.shp")
        self._touch("data.gdb", "leftover.dbf")
        self._touch("data.gdb", "leftover.shx")

        result = _find_geodata_files(self.start_folder)

        # production code normalizes with os.path.abspath(), not Path.resolve() -
        # the latter also expands Windows 8.3 short names (e.g. RUNNER~1), which
        # would make this comparison fail on GitHub Actions Windows runners.
        self.assertEqual(result["filegdb"], (str(gdb_dir),))
        # only data.gdb itself is counted, not its internal subfolder
        self.assertEqual(result["num_folders"], 1)
        # the shapefile-looking file inside the .gdb is never visited
        self.assertEqual(result["shp"], ())

    def test_geopackage_and_spatialite_are_grouped_into_fdb(self):
        """GeoPackage and Spatialite files are merged into the fdb bucket."""
        gpkg = self._touch("catalog.gpkg")
        sqlite = self._touch("catalog.sqlite")

        result = _find_geodata_files(self.start_folder)

        self.assertEqual(result["geopackage"], (str(gpkg),))
        self.assertEqual(result["spatialite"], (str(sqlite),))
        self.assertEqual(set(result["fdb"]), {str(gpkg), str(sqlite)})

    # -- ordering -------------------------------------------------------------

    def test_results_are_sorted(self):
        """Files of a same format are returned in sorted path order."""
        zeta = self._touch("zeta.gml")
        alpha = self._touch("alpha.gml")

        result = _find_geodata_files(self.start_folder)

        self.assertEqual(result["gml"], tuple(sorted([str(zeta), str(alpha)])))

    # -- known limitation: raster extensions ---------------------------------

    def test_geotiff_literal_extension_is_detected(self):
        """A file literally extensioned '.geotiff' is bucketed as raster."""
        geotiff = self._touch("ortho.geotiff")

        result = _find_geodata_files(self.start_folder)

        self.assertEqual(result["geotiff"], [str(geotiff)])
        self.assertIn(str(geotiff), result["raster"])

    def test_common_geotiff_extensions_are_detected(self):
        """.tif and .tiff (the real-world GeoTIFF extensions) are bucketed
        as geotiff/raster, alongside the literal '.geotiff' extension."""
        tif = self._touch("ortho.tif")
        tiff = self._touch("ortho2.tiff")

        result = _find_geodata_files(self.start_folder)

        self.assertEqual(set(result["geotiff"]), {str(tif), str(tiff)})
        self.assertIn(str(tif), result["raster"])
        self.assertIn(str(tiff), result["raster"])

    def test_other_formatsraster_extensions_are_detected(self):
        """.ecw and .jpeg, declared in the FormatsRaster enum, are bucketed
        as raster through the generic FormatsRaster.has_value() fallback."""
        ecw = self._touch("ortho.ecw")
        jpeg = self._touch("ortho.jpeg")

        result = _find_geodata_files(self.start_folder)

        self.assertEqual(set(result["raster"]), {str(ecw), str(jpeg)})
        self.assertEqual(result["geotiff"], [])


# ############################################################################
# ####### Stand-alone run ########
# ################################
if __name__ == "__main__":
    unittest.main()
