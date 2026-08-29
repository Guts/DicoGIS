#! python3  # noqa: E265

"""
Usage from the repo root folder:
    python -m pytest tests/test_georeaders_process_files.py
"""

# #############################################################################
# ########## Libraries #############
# ##################################

# Standard library
from pathlib import Path
from unittest.mock import MagicMock

# 3rd party
import pytest

# package
from dicogis.georeaders.process_files import DatasetToProcess, ProcessingFiles

# #############################################################################
# ########## Functions #############
# ##################################


def _make_processor(*, opt_quick_fail: bool, progress_reporter) -> ProcessingFiles:
    """Build a minimal ProcessingFiles instance for unit testing.

    Only the arguments relevant to export_metadataset are meaningful; the file
    lists are left empty since no listing/counting is exercised here.
    """
    return ProcessingFiles(
        serializer=MagicMock(),
        localized_strings={},
        li_cdao=[],
        li_dxf=[],
        li_flat_geodatabase_esri_filegdb=[],
        li_flat_geodatabase_geopackage=[],
        li_flat_geodatabase_spatialite=[],
        li_geojson=[],
        li_geotiff=[],
        li_gxt=[],
        li_gml=[],
        li_kml=[],
        li_mapinfo_tab=[],
        li_shapefiles=[],
        li_vectors=[],
        li_rasters=[],
        li_file_databases=[],
        progress_reporter=progress_reporter,
        opt_quick_fail=opt_quick_fail,
    )


# #############################################################################
# ########## Classes ###############
# ##################################


class TestExportMetadataset:
    """Test ProcessingFiles.export_metadataset progress reporting."""

    @pytest.mark.parametrize("opt_quick_fail", [True, False])
    def test_export_metadataset_reports_progress_once_per_call(self, opt_quick_fail):
        """The 'exporting...' message must be emitted exactly once per call, not
        duplicated between the quick-fail and normal code paths."""
        progress_reporter = MagicMock()
        processor = _make_processor(
            opt_quick_fail=opt_quick_fail, progress_reporter=progress_reporter
        )
        dataset = DatasetToProcess(
            file_path=Path("/tmp/some/folder/sample.shp"),
            file_format="esri_shapefile",
            georeader=object,
        )
        metadataset = MagicMock()

        result_dataset, result_metadataset = processor.export_metadataset(
            dataset_to_process=dataset, metadataset_to_serialize=metadataset
        )

        assert result_dataset.exported is True
        assert result_metadataset is metadataset
        processor.serializer.serialize_metadaset.assert_called_once_with(
            metadataset=metadataset
        )

        displayed_messages = [
            call.args[0] for call in progress_reporter.set_message.call_args_list
        ]
        assert displayed_messages == [
            "Exporting metadata of sample.shp...",
            "Metadata of sample.shp: EXPORTED",
        ]
        progress_reporter.increment.assert_called_once()

    @pytest.mark.parametrize("opt_quick_fail", [True, False])
    def test_export_metadataset_uses_file_name_not_full_path(self, opt_quick_fail):
        """Progress messages should stay short: use the file name, not the full
        (possibly long) path."""
        progress_reporter = MagicMock()
        processor = _make_processor(
            opt_quick_fail=opt_quick_fail, progress_reporter=progress_reporter
        )
        long_path = Path("/some/deeply/nested/folder/tree/dataset.gpkg")
        dataset = DatasetToProcess(
            file_path=long_path,
            file_format="file_geodatabase_geopackage",
            georeader=object,
        )

        processor.export_metadataset(
            dataset_to_process=dataset, metadataset_to_serialize=MagicMock()
        )

        for call in progress_reporter.set_message.call_args_list:
            assert str(long_path) not in call.args[0]
            assert long_path.name in call.args[0]

    def test_export_metadataset_without_progress_reporter_does_not_raise(self):
        """No progress_reporter (e.g. CLI usage) must be a silent no-op."""
        processor = _make_processor(opt_quick_fail=False, progress_reporter=None)
        dataset = DatasetToProcess(
            file_path=Path("sample.geojson"),
            file_format="geojson",
            georeader=object,
        )

        result_dataset, _ = processor.export_metadataset(
            dataset_to_process=dataset, metadataset_to_serialize=MagicMock()
        )

        assert result_dataset.exported is True
        processor.serializer.serialize_metadaset.assert_called_once()
