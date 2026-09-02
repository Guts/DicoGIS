#! python3  # noqa E265

"""
Usage from the repo root folder:

.. code-block:: bash
    # for whole tests
    python -m unittest tests.test_cli_inventory
    # for specific test
    python -m unittest tests.test_cli_inventory.TestDetermineOutputPath.test_explicit_output_path_wins
"""

# standard library
import sys
import types
import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

# 3rd party
import typer

# project
from dicogis.cli.cmd_inventory import determine_output_path, inventory
from dicogis.models.metadataset import MetaDatabaseTable


# ############################################################################
# ########## Globals #############
# ################################


def _stub_georeader_modules(processing_files_mock=None, read_postgis_mock=None):
    """Install fake dicogis.georeaders.process_files/read_postgis modules in
    sys.modules so inventory()'s deferred, GDAL-gated imports succeed
    without a real GDAL install, and so ProcessingFiles/ReadPostGIS can be
    inspected/controlled from the test.
    """
    process_files_module = types.ModuleType("dicogis.georeaders.process_files")
    process_files_module.ProcessingFiles = (
        processing_files_mock if processing_files_mock is not None else MagicMock()
    )
    read_postgis_module = types.ModuleType("dicogis.georeaders.read_postgis")
    read_postgis_module.ReadPostGIS = (
        read_postgis_mock if read_postgis_mock is not None else MagicMock()
    )
    return patch.dict(
        sys.modules,
        {
            "dicogis.georeaders.process_files": process_files_module,
            "dicogis.georeaders.read_postgis": read_postgis_module,
        },
    )


# ############################################################################
# ########## Classes #############
# ################################


class TestDetermineOutputPath(unittest.TestCase):
    """Test determine_output_path()."""

    def test_explicit_output_path_wins_over_everything_else(self):
        result = determine_output_path(
            output_path=Path("explicit.xlsx"),
            output_format="excel",
            input_folder=Path("some/folder"),
        )

        self.assertEqual(result, Path("explicit.xlsx"))

    def test_excel_default_name_from_input_folder(self):
        result = determine_output_path(
            output_path=None,
            output_format="excel",
            input_folder=Path("some/folder"),
        )

        self.assertEqual(result, Path(f"DicoGIS_folder_{date.today()}.xlsx"))

    def test_excel_default_name_from_pg_services(self):
        result = determine_output_path(
            output_path=None,
            output_format="excel",
            pg_services=["srv_a", "srv_b"],
        )

        self.assertEqual(
            result, Path(f"DicoGIS_PostGIS_srv_a__srv_b_{date.today()}.xlsx")
        )

    def test_json_default_name_is_a_folder_without_extension(self):
        result = determine_output_path(
            output_path=None,
            output_format="json",
            input_folder=Path("some/folder"),
        )

        self.assertEqual(result, Path(f"DicoGIS_folder_{date.today()}"))

    def test_udata_default_name_is_a_folder_without_extension(self):
        result = determine_output_path(
            output_path=None,
            output_format="udata",
            input_folder=Path("some/folder"),
        )

        self.assertEqual(result, Path(f"DicoGIS_folder_{date.today()}"))

    def test_json_default_name_from_pg_services(self):
        result = determine_output_path(
            output_path=None,
            output_format="json",
            pg_services=["srv_a"],
        )

        self.assertEqual(result, Path(f"DicoGIS_srv_a_{date.today()}"))

    def test_unsupported_format_without_explicit_path_raises_valueerror(self):
        with self.assertRaises(ValueError):
            determine_output_path(
                output_path=None,
                output_format="bogus",
                input_folder=Path("some/folder"),
            )

    def test_known_gap_no_folder_and_no_pg_services_returns_none(self):
        """Document a gap: with no output_path, no input_folder and no
        pg_services, the function falls through every branch and returns
        None instead of a Path or raising. inventory() never hits this in
        practice because it validates that at least one of input_folder/
        pg_services is set before calling determine_output_path()."""
        result = determine_output_path(
            output_path=None,
            output_format="excel",
            input_folder=None,
            pg_services=None,
        )

        self.assertIsNone(result)


class TestInventoryEarlyValidation(unittest.TestCase):
    """Test inventory()'s guard clauses that run before any GDAL-gated import."""

    def test_missing_input_folder_and_pg_services_exits(self):
        with self.assertRaises(typer.Exit) as raised:
            inventory(input_folder=None, pg_services=None)

        self.assertEqual(raised.exception.exit_code, 1)

    @patch("dicogis.cli.cmd_inventory.GDAL_IS_AVAILABLE", False)
    def test_gdal_unavailable_exits(self):
        with TemporaryDirectory(ignore_cleanup_errors=True) as tmpdirname:
            with self.assertRaises(typer.Exit) as raised:
                inventory(input_folder=Path(tmpdirname))

        self.assertEqual(raised.exception.exit_code, 1)


class TestInventoryFormatFlagDerivation(unittest.TestCase):
    """Test how inventory() derives ProcessingFiles' opt_analyze_* flags
    from the --formats option (a comma-joined string checked with `in`)."""

    def _run_with_formats(self, formats: str, processing_files_mock: MagicMock):
        with TemporaryDirectory(ignore_cleanup_errors=True) as tmpdirname:
            input_folder = Path(tmpdirname)
            # at least one real dataset, or inventory() exits before ever
            # instantiating ProcessingFiles
            for suffix in (".shp", ".dbf", ".shx"):
                (input_folder / f"parcels{suffix}").touch()
            output_path = input_folder / "out.xlsx"
            with (
                patch("dicogis.cli.cmd_inventory.GDAL_IS_AVAILABLE", True),
                patch("dicogis.cli.cmd_inventory.send_system_notify"),
                _stub_georeader_modules(processing_files_mock=processing_files_mock),
            ):
                inventory(
                    input_folder=input_folder,
                    formats=formats,
                    output_path=output_path,
                    output_format="excel",
                    language="EN",
                    opt_open_output=False,
                )

    def test_mapinfo_tab_flag_matches_mapinfo_tab_format(self):
        """opt_analyze_mapinfo_tab is derived from "mapinfo_tab" in formats
        (previously checked "geojson" instead, a copy-paste artifact)."""
        processing_files_mock = MagicMock()
        processing_files_mock.return_value.count_files_to_process.return_value = 0

        # mapinfo_tab requested, geojson excluded: MapInfo TAB analysis
        # must be enabled regardless of geojson's presence.
        self._run_with_formats("mapinfo_tab,esri_shapefile", processing_files_mock)

        _, kwargs = processing_files_mock.call_args
        self.assertTrue(kwargs["opt_analyze_mapinfo_tab"])

    def test_cdao_flag_matches_default_formats(self):
        """opt_analyze_cdao is derived from "dgn" in formats (the actual
        SUPPORTED_FORMATS member representing CAD/DAO; previously checked
        "dxf", which is never a member name, so it never matched)."""
        from dicogis.constants import SUPPORTED_FORMATS

        default_formats = ",".join(f.name for f in SUPPORTED_FORMATS)
        self.assertIn("dgn", default_formats)

        processing_files_mock = MagicMock()
        processing_files_mock.return_value.count_files_to_process.return_value = 0

        self._run_with_formats(default_formats, processing_files_mock)

        _, kwargs = processing_files_mock.call_args
        self.assertTrue(kwargs["opt_analyze_cdao"])

    def test_unsupported_format_is_dropped_with_a_warning(self):
        """A requested format whose GDAL driver isn't installed (e.g.
        Geoconcept, an optional/plugin driver) is dropped from `formats`
        before deriving opt_analyze_* flags, instead of failing later while
        actually processing files."""
        processing_files_mock = MagicMock()
        processing_files_mock.return_value.count_files_to_process.return_value = 0

        def fake_is_supported(format_name, available_drivers=None):
            return format_name != "gxt"

        with patch(
            "dicogis.cli.cmd_inventory.is_format_supported_by_gdal",
            side_effect=fake_is_supported,
        ):
            self._run_with_formats("esri_shapefile,gxt", processing_files_mock)

        _, kwargs = processing_files_mock.call_args
        self.assertFalse(kwargs["opt_analyze_gxt"])
        self.assertTrue(kwargs["opt_analyze_shapefiles"])

    def test_supported_formats_are_all_kept(self):
        """When every requested format is reported as supported, none is
        dropped."""
        processing_files_mock = MagicMock()
        processing_files_mock.return_value.count_files_to_process.return_value = 0

        with patch(
            "dicogis.cli.cmd_inventory.is_format_supported_by_gdal",
            return_value=True,
        ):
            self._run_with_formats("esri_shapefile,gxt", processing_files_mock)

        _, kwargs = processing_files_mock.call_args
        self.assertTrue(kwargs["opt_analyze_gxt"])
        self.assertTrue(kwargs["opt_analyze_shapefiles"])


class TestInventoryParallelScanOptions(unittest.TestCase):
    """Test that --opt-parallel-scan/--listing-max-workers (and their
    DICOGIS_LISTING_PARALLEL_SCAN/DICOGIS_LISTING_MAX_WORKERS env vars, via
    Typer's envvar= support) are forwarded to find_geodata_files()."""

    # a find_geodata_files()-shaped, all-empty result: (num_folders, then 16
    # per-format lists/tuples in its documented return order)
    _EMPTY_FIND_RESULT = (
        0,
        (),
        (),
        (),
        (),
        (),
        [],
        (),
        [],
        (),
        (),
        (),
        (),
        (),
        (),
        (),
        (),
    )

    def test_parallel_scan_and_max_workers_are_forwarded(self):
        with TemporaryDirectory(ignore_cleanup_errors=True) as tmpdirname:
            input_folder = Path(tmpdirname)
            output_path = input_folder / "out.xlsx"

            with (
                patch("dicogis.cli.cmd_inventory.GDAL_IS_AVAILABLE", True),
                patch(
                    "dicogis.cli.cmd_inventory.find_geodata_files",
                    return_value=self._EMPTY_FIND_RESULT,
                ) as mock_find,
                _stub_georeader_modules(),
                self.assertRaises(typer.Exit),
            ):
                inventory(
                    input_folder=input_folder,
                    output_path=output_path,
                    output_format="excel",
                    language="EN",
                    opt_parallel_scan=True,
                    listing_max_workers=4,
                )

        mock_find.assert_called_once_with(
            start_folder=input_folder, parallel_scan=True, max_workers=4
        )

    def test_defaults_are_off_and_auto(self):
        """Without the flags, parallel_scan defaults to False and
        max_workers to None (ThreadPoolExecutor's own auto-sized default)."""
        with TemporaryDirectory(ignore_cleanup_errors=True) as tmpdirname:
            input_folder = Path(tmpdirname)
            output_path = input_folder / "out.xlsx"

            with (
                patch("dicogis.cli.cmd_inventory.GDAL_IS_AVAILABLE", True),
                patch(
                    "dicogis.cli.cmd_inventory.find_geodata_files",
                    return_value=self._EMPTY_FIND_RESULT,
                ) as mock_find,
                _stub_georeader_modules(),
                self.assertRaises(typer.Exit),
            ):
                inventory(
                    input_folder=input_folder,
                    output_path=output_path,
                    output_format="excel",
                    language="EN",
                )

        mock_find.assert_called_once_with(
            start_folder=input_folder, parallel_scan=False, max_workers=None
        )


class TestInventoryNoDataFound(unittest.TestCase):
    """Test inventory()'s behavior when the input folder has no geodata."""

    def test_nodata_branch_exits_without_calling_processing_files(self):
        """When no geodata is found, inventory() now actually raises
        typer.Exit(1) instead of constructing and discarding it, so
        ProcessingFiles is never instantiated."""
        processing_files_mock = MagicMock()
        processing_files_mock.return_value.count_files_to_process.return_value = 0

        with TemporaryDirectory(ignore_cleanup_errors=True) as tmpdirname:
            input_folder = Path(tmpdirname)  # empty: no geodata files at all
            output_path = input_folder / "out.xlsx"
            with (
                patch("dicogis.cli.cmd_inventory.GDAL_IS_AVAILABLE", True),
                patch("dicogis.cli.cmd_inventory.send_system_notify"),
                _stub_georeader_modules(processing_files_mock=processing_files_mock),
                self.assertRaises(typer.Exit) as raised,
            ):
                inventory(
                    input_folder=input_folder,
                    output_path=output_path,
                    output_format="excel",
                    language="EN",
                    opt_open_output=False,
                )

        self.assertEqual(raised.exception.exit_code, 1)
        processing_files_mock.assert_not_called()


class TestInventoryHappyPath(unittest.TestCase):
    """Test inventory()'s orchestration when geodata files are found."""

    def _make_shapefile_trio(self, folder: Path) -> None:
        for suffix in (".shp", ".dbf", ".shx"):
            (folder / f"parcels{suffix}").touch()

    def test_processing_files_is_driven_and_notified(self):
        processing_files_mock = MagicMock()
        processing_files_mock.return_value.count_files_to_process.return_value = 1

        with TemporaryDirectory(ignore_cleanup_errors=True) as tmpdirname:
            input_folder = Path(tmpdirname)
            self._make_shapefile_trio(input_folder)
            output_path = input_folder / "out.xlsx"

            with (
                patch("dicogis.cli.cmd_inventory.GDAL_IS_AVAILABLE", True),
                patch("dicogis.cli.cmd_inventory.send_system_notify") as mock_notify,
                patch("typer.launch") as mock_launch,
                _stub_georeader_modules(processing_files_mock=processing_files_mock),
            ):
                inventory(
                    input_folder=input_folder,
                    output_path=output_path,
                    output_format="excel",
                    language="EN",
                    opt_open_output=True,
                    opt_notify_sound=False,
                )

        processing_files_mock.assert_called_once()
        _, kwargs = processing_files_mock.call_args
        self.assertEqual(kwargs["li_shapefiles"], (str(input_folder / "parcels.shp"),))
        self.assertTrue(kwargs["opt_analyze_shapefiles"])

        processing_files_mock.return_value.count_files_to_process.assert_called_once()
        processing_files_mock.return_value.process_datasets_in_queue.assert_called_once()

        mock_notify.assert_called_once()
        self.assertEqual(mock_notify.call_args.kwargs["notification_sound"], False)
        mock_launch.assert_called_once_with(url=f"{output_path.resolve()}")

    def test_opt_open_output_false_does_not_launch(self):
        processing_files_mock = MagicMock()
        processing_files_mock.return_value.count_files_to_process.return_value = 1

        with TemporaryDirectory(ignore_cleanup_errors=True) as tmpdirname:
            input_folder = Path(tmpdirname)
            self._make_shapefile_trio(input_folder)
            output_path = input_folder / "out.xlsx"

            with (
                patch("dicogis.cli.cmd_inventory.GDAL_IS_AVAILABLE", True),
                patch("dicogis.cli.cmd_inventory.send_system_notify"),
                patch("typer.launch") as mock_launch,
                _stub_georeader_modules(processing_files_mock=processing_files_mock),
            ):
                inventory(
                    input_folder=input_folder,
                    output_path=output_path,
                    output_format="excel",
                    language="EN",
                    opt_open_output=False,
                )

        mock_launch.assert_not_called()


class TestInventoryPgServices(unittest.TestCase):
    """Test inventory()'s PostgreSQL-services branch."""

    @patch("dicogis.cli.cmd_inventory.check_usable_pg_services", return_value=[])
    def test_no_usable_pg_service_exits(self, mock_check):
        with TemporaryDirectory(ignore_cleanup_errors=True) as tmpdirname:
            with (
                patch("dicogis.cli.cmd_inventory.GDAL_IS_AVAILABLE", True),
                _stub_georeader_modules(),
                self.assertRaises(typer.Exit) as raised,
            ):
                inventory(
                    input_folder=None,
                    pg_services=["not_a_real_service"],
                    output_path=Path(tmpdirname) / "out.xlsx",
                    language="EN",
                )

        self.assertEqual(raised.exception.exit_code, 1)

    def test_usable_pg_service_is_processed_and_notified(self):
        fake_layer = MagicMock()
        fake_conn = MagicMock()
        fake_conn.GetLayerCount.return_value = 1
        fake_conn.GetLayerByIndex.return_value = fake_layer

        read_postgis_mock = MagicMock()
        fake_reader = read_postgis_mock.return_value
        fake_reader.conn = fake_conn
        fake_metadataset = MetaDatabaseTable(
            name="public.roads", dataset_type="sgbd_postgis"
        )
        fake_reader.infos_dataset.return_value = fake_metadataset

        with TemporaryDirectory(ignore_cleanup_errors=True) as tmpdirname:
            output_path = Path(tmpdirname) / "out.xlsx"
            with (
                patch("dicogis.cli.cmd_inventory.GDAL_IS_AVAILABLE", True),
                patch(
                    "dicogis.cli.cmd_inventory.check_usable_pg_services",
                    return_value=["srv_a"],
                ),
                patch("dicogis.cli.cmd_inventory.send_system_notify") as mock_notify,
                patch("typer.launch"),
                _stub_georeader_modules(read_postgis_mock=read_postgis_mock),
            ):
                inventory(
                    input_folder=None,
                    pg_services=["srv_a"],
                    output_path=output_path,
                    output_format="excel",
                    language="EN",
                    opt_open_output=False,
                )

        read_postgis_mock.assert_called_once_with(service="srv_a")
        fake_reader.infos_dataset.assert_called_once_with(layer=fake_layer)
        mock_notify.assert_called_once()

    @staticmethod
    def _fake_reader(layers_count: int | None):
        """Build a stub ReadPostGIS instance.

        layers_count None means the connection failed: get_connection() leaves
        `conn` at None and the reason is read from db_connection.state_msg.
        """
        fake_reader = MagicMock()
        if layers_count is None:
            fake_reader.conn = None
            fake_reader.db_connection.state_msg = "connection refused"
            return fake_reader

        fake_conn = MagicMock()
        fake_conn.GetLayerCount.return_value = layers_count
        fake_conn.GetLayerByIndex.side_effect = lambda index: MagicMock(
            name=f"l{index}"
        )
        fake_reader.conn = fake_conn
        fake_reader.infos_dataset.side_effect = lambda layer: MetaDatabaseTable(
            name="public.roads", dataset_type="sgbd_postgis"
        )
        return fake_reader

    def _run_with_services(self, services_layers: dict[str, int | None]):
        """Run inventory() over several stubbed services.

        Maps each service name to its layer count, or to None for a service
        whose connection fails.

        Returns:
            the send_system_notify mock, whether the output file was written
            (checked before the temporary folder is cleaned up) and the exit
            code, 0 when inventory() returned without raising typer.Exit.
        """
        read_postgis_mock = MagicMock()
        read_postgis_mock.side_effect = [
            self._fake_reader(layers_count) for layers_count in services_layers.values()
        ]
        exit_code = 0

        with TemporaryDirectory(ignore_cleanup_errors=True) as tmpdirname:
            output_path = Path(tmpdirname) / "out.xlsx"
            with (
                patch("dicogis.cli.cmd_inventory.GDAL_IS_AVAILABLE", True),
                patch(
                    "dicogis.cli.cmd_inventory.check_usable_pg_services",
                    return_value=list(services_layers),
                ),
                patch("dicogis.cli.cmd_inventory.send_system_notify") as mock_notify,
                patch("typer.launch"),
                _stub_georeader_modules(read_postgis_mock=read_postgis_mock),
            ):
                try:
                    inventory(
                        input_folder=None,
                        pg_services=list(services_layers),
                        output_path=output_path,
                        output_format="excel",
                        language="EN",
                        opt_open_output=False,
                    )
                except typer.Exit as err:
                    exit_code = err.exit_code

            # inside the context manager: the folder is gone right after
            output_written = output_path.is_file()

        return mock_notify, output_written, exit_code

    def test_notification_counts_layers_of_every_service(self):
        """Regression: the count was read back from the last reader only, so
        tables inventoried through the other services went unreported."""
        mock_notify, _, exit_code = self._run_with_services({"srv_a": 2, "srv_b": 3})

        self.assertEqual(exit_code, 0)
        self.assertIn(
            "5 PostGIS tables", mock_notify.call_args.kwargs["notification_message"]
        )

    def test_last_service_failing_to_connect_does_not_crash(self):
        """Regression: the final notification dereferenced the last reader's
        `conn`, which a failed connection leaves at None -- an AttributeError
        at the very end of an otherwise successful run."""
        mock_notify, output_written, exit_code = self._run_with_services(
            {"srv_ok": 2, "srv_ko": None}
        )

        self.assertEqual(exit_code, 0)
        self.assertIn(
            "2 PostGIS tables", mock_notify.call_args.kwargs["notification_message"]
        )
        self.assertTrue(output_written)

    def test_every_service_failing_exits_without_writing_the_output(self):
        """Nothing could be read: exit non-zero rather than report success over
        an empty workbook, which a calling script would take at face value."""
        mock_notify, output_written, exit_code = self._run_with_services(
            {"srv_ko_1": None, "srv_ko_2": None}
        )

        self.assertEqual(exit_code, 1)
        mock_notify.assert_not_called()
        self.assertFalse(output_written)


# ############################################################################
# ####### Stand-alone run ########
# ################################
if __name__ == "__main__":
    unittest.main()
