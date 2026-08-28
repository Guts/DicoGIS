#! python3  # noqa E265

"""
Usage from the repo root folder:

.. code-block:: bash
    # for whole tests
    python -m unittest tests.test_process_files
    # for specific test
    python -m unittest tests.test_process_files.TestReadDataset.test_success_marks_processed_and_returns_metadataset
"""

# standard library
import unittest
from unittest.mock import MagicMock

# project
from dicogis.export.base_serializer import MetadatasetSerializerBase
from dicogis.georeaders.process_files import DatasetToProcess, ProcessingFiles
from dicogis.models.metadataset import MetaDataset

# ############################################################################
# ########## Globals #############
# ################################


class FakeSerializer(MetadatasetSerializerBase):
    """In-memory serializer recording calls instead of writing any file."""

    def __init__(self, fail_on_serialize: bool = False):
        super().__init__(localized_strings={})
        self.fail_on_serialize = fail_on_serialize
        self.pre_serializing_calls: list[dict] = []
        self.serialize_calls: list[MetaDataset] = []
        self.post_serializing_call_count = 0

    def pre_serializing(self, **kwargs):
        self.pre_serializing_calls.append(kwargs)

    def post_serializing(self, **kwargs):
        self.post_serializing_call_count += 1

    def serialize_metadaset(self, metadataset: MetaDataset) -> None:
        if self.fail_on_serialize:
            raise RuntimeError("boom exporting dataset")
        self.serialize_calls.append(metadataset)


class SucceedingGeoReader:
    """Fake georeader returning a canned MetaDataset."""

    def infos_dataset(self, source_path: str) -> MetaDataset:
        return MetaDataset(name=source_path)


class FailingGeoReader:
    """Fake georeader that always raises while reading."""

    def infos_dataset(self, source_path: str) -> MetaDataset:
        raise RuntimeError("boom reading dataset")


def _make_processor(serializer: MetadatasetSerializerBase | None = None, **overrides):
    """Build a ProcessingFiles with every file-list empty by default."""
    kwargs = dict(
        serializer=serializer if serializer is not None else FakeSerializer(),
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
    )
    kwargs.update(overrides)
    return ProcessingFiles(**kwargs)


# ############################################################################
# ########## Classes #############
# ################################


class TestReadDataset(unittest.TestCase):
    """Test ProcessingFiles.read_dataset()."""

    def test_success_marks_processed_and_returns_metadataset(self):
        """A successful read marks the dataset processed and returns metadata."""
        processor = _make_processor()
        dataset = DatasetToProcess(
            file_path="parcels.shp",
            file_format="esri_shapefile",
            georeader=SucceedingGeoReader,
        )

        result_dataset, metadataset = processor.read_dataset(dataset_to_process=dataset)

        self.assertTrue(result_dataset.processed)
        self.assertIsNone(result_dataset.process_error)
        self.assertIsInstance(metadataset, MetaDataset)

    def test_failure_is_caught_and_recorded_when_not_quick_fail(self):
        """A reading error is swallowed: dataset is marked processed with an error."""
        processor = _make_processor(opt_quick_fail=False)
        dataset = DatasetToProcess(
            file_path="broken.shp",
            file_format="esri_shapefile",
            georeader=FailingGeoReader,
        )

        result_dataset, metadataset = processor.read_dataset(dataset_to_process=dataset)

        self.assertTrue(result_dataset.processed)
        self.assertIsNotNone(result_dataset.process_error)
        self.assertIsNone(metadataset)

    def test_quick_fail_propagates_exception(self):
        """With opt_quick_fail, a reading error is not caught."""
        processor = _make_processor(opt_quick_fail=True)
        dataset = DatasetToProcess(
            file_path="broken.shp",
            file_format="esri_shapefile",
            georeader=FailingGeoReader,
        )

        with self.assertRaises(RuntimeError):
            processor.read_dataset(dataset_to_process=dataset)

    def test_works_without_a_progress_reporter(self):
        """No progress_reporter configured must not raise."""
        processor = _make_processor(progress_reporter=None)
        dataset = DatasetToProcess(
            file_path="parcels.shp",
            file_format="esri_shapefile",
            georeader=SucceedingGeoReader,
        )

        # should not raise
        processor.read_dataset(dataset_to_process=dataset)

    def test_progress_reporter_receives_message_and_increment(self):
        """A configured progress_reporter is updated on success."""
        reporter = MagicMock()
        processor = _make_processor(progress_reporter=reporter)
        dataset = DatasetToProcess(
            file_path="parcels.shp",
            file_format="esri_shapefile",
            georeader=SucceedingGeoReader,
        )

        processor.read_dataset(dataset_to_process=dataset)

        self.assertGreaterEqual(reporter.set_message.call_count, 2)
        reporter.increment.assert_called_once()


class TestExportMetadataset(unittest.TestCase):
    """Test ProcessingFiles.export_metadataset()."""

    def test_success_calls_serializer_and_marks_exported(self):
        """A successful export marks the dataset exported and serializes it."""
        serializer = FakeSerializer()
        processor = _make_processor(serializer=serializer)
        dataset = DatasetToProcess(
            file_path="parcels.shp", file_format="esri_shapefile", georeader=object
        )
        metadataset = MetaDataset(name="parcels")

        result_dataset, _ = processor.export_metadataset(
            dataset_to_process=dataset, metadataset_to_serialize=metadataset
        )

        self.assertTrue(result_dataset.exported)
        self.assertEqual(serializer.serialize_calls, [metadataset])

    def test_quick_fail_propagates_exception(self):
        """With opt_quick_fail, a serialization error is not caught."""
        serializer = FakeSerializer(fail_on_serialize=True)
        processor = _make_processor(serializer=serializer, opt_quick_fail=True)
        dataset = DatasetToProcess(
            file_path="parcels.shp", file_format="esri_shapefile", georeader=object
        )

        with self.assertRaises(RuntimeError):
            processor.export_metadataset(
                dataset_to_process=dataset,
                metadataset_to_serialize=MetaDataset(name="parcels"),
            )

    def test_known_bug_failure_overwrites_exported_instead_of_export_error(self):
        """Document current (likely unintended) behavior on export failure.

        The except branch in ``export_metadataset`` does::

            dataset_to_process.exported = False
            dataset_to_process.exported = err

        instead of setting ``dataset_to_process.export_error = err`` on the
        second line. As a result, after a failed export ``exported`` ends up
        holding the *exception instance* (truthy, so it reads as "exported
        successfully" in a boolean context) rather than staying False, and
        ``export_error`` -- the field meant to carry this information -- is
        never populated. This test pins that behavior; if the typo is fixed,
        update this test to assert ``exported is False`` and
        ``export_error is err`` instead.
        """
        serializer = FakeSerializer(fail_on_serialize=True)
        processor = _make_processor(serializer=serializer, opt_quick_fail=False)
        dataset = DatasetToProcess(
            file_path="parcels.shp", file_format="esri_shapefile", georeader=object
        )

        result_dataset, _ = processor.export_metadataset(
            dataset_to_process=dataset,
            metadataset_to_serialize=MetaDataset(name="parcels"),
        )

        self.assertIsInstance(result_dataset.exported, RuntimeError)
        self.assertIsNone(result_dataset.export_error)


class TestProcessDatasetsInQueue(unittest.TestCase):
    """Test ProcessingFiles.process_datasets_in_queue()."""

    def test_already_processed_dataset_is_skipped(self):
        """A dataset already marked processed is left untouched."""
        serializer = FakeSerializer()
        processor = _make_processor(serializer=serializer)
        dataset = DatasetToProcess(
            file_path="parcels.shp",
            file_format="esri_shapefile",
            georeader=SucceedingGeoReader,
            processed=True,
        )
        processor.li_files_to_process = [dataset]

        processor.process_datasets_in_queue()

        self.assertEqual(serializer.serialize_calls, [])
        self.assertEqual(serializer.post_serializing_call_count, 1)

    def test_dataset_that_fails_to_read_is_not_exported(self):
        """When reading fails, the dataset is never handed to the serializer."""
        serializer = FakeSerializer()
        processor = _make_processor(serializer=serializer)
        dataset = DatasetToProcess(
            file_path="broken.shp",
            file_format="esri_shapefile",
            georeader=FailingGeoReader,
        )
        processor.li_files_to_process = [dataset]

        processor.process_datasets_in_queue()

        self.assertEqual(serializer.serialize_calls, [])
        self.assertFalse(dataset.exported)

    def test_successful_dataset_is_read_and_exported(self):
        """A dataset that reads successfully is serialized."""
        serializer = FakeSerializer()
        processor = _make_processor(serializer=serializer)
        dataset = DatasetToProcess(
            file_path="parcels.shp",
            file_format="esri_shapefile",
            georeader=SucceedingGeoReader,
        )
        processor.li_files_to_process = [dataset]

        processor.process_datasets_in_queue()

        self.assertTrue(dataset.exported)
        self.assertEqual(len(serializer.serialize_calls), 1)

    def test_post_serializing_called_even_with_empty_queue(self):
        """post_serializing() runs even when there is nothing to process."""
        serializer = FakeSerializer()
        processor = _make_processor(serializer=serializer)

        processor.process_datasets_in_queue()

        self.assertEqual(serializer.post_serializing_call_count, 1)


class TestAddFilesToProcessQueue(unittest.TestCase):
    """Test ProcessingFiles.add_files_to_process_queue()."""

    def test_adds_datasets_with_resolved_georeader(self):
        """Datasets are queued with the georeader mapped for their format."""
        processor = _make_processor()

        added = processor.add_files_to_process_queue(
            list_of_datasets=["a.shp", "b.shp"], dataset_format="esri_shapefile"
        )

        self.assertEqual(len(added), 2)
        self.assertEqual(processor.li_files_to_process, added)
        for dataset in added:
            self.assertIs(
                dataset.georeader,
                ProcessingFiles.MATRIX_FORMAT_GEOREADER["esri_shapefile"],
            )

    def test_accumulates_across_multiple_calls(self):
        """Repeated calls append to the same processing queue."""
        processor = _make_processor()

        processor.add_files_to_process_queue(
            list_of_datasets=["a.shp"], dataset_format="esri_shapefile"
        )
        processor.add_files_to_process_queue(
            list_of_datasets=["b.kml"], dataset_format="kml"
        )

        self.assertEqual(len(processor.li_files_to_process), 2)

    def test_unmapped_format_resolves_to_none_georeader(self):
        """An unregistered format resolves to a None georeader (dict.get default)."""
        processor = _make_processor()

        added = processor.add_files_to_process_queue(
            list_of_datasets=["plan.dxf"], dataset_format="not_a_registered_format"
        )

        self.assertIsNone(added[0].georeader)


class TestCountFilesToProcess(unittest.TestCase):
    """Test ProcessingFiles.count_files_to_process()."""

    def test_disabled_option_is_not_counted_or_queued(self):
        """A format whose analysis flag is off contributes nothing."""
        processor = _make_processor(
            li_shapefiles=["a.shp", "b.shp"], opt_analyze_shapefiles=False
        )

        total = processor.count_files_to_process()

        self.assertEqual(total, 0)
        self.assertEqual(processor.li_files_to_process, [])

    def test_enabled_formats_are_summed_and_queued(self):
        """Multiple enabled formats are summed into total_files and queued."""
        serializer = FakeSerializer()
        processor = _make_processor(
            serializer=serializer,
            li_shapefiles=["a.shp"],
            li_kml=["b.kml", "c.kml"],
        )

        total = processor.count_files_to_process()

        self.assertEqual(total, 3)
        self.assertEqual(processor.total_files, 3)
        self.assertEqual(len(processor.li_files_to_process), 3)
        self.assertTrue(
            any(call.get("has_vector") for call in serializer.pre_serializing_calls)
        )

    def test_raster_option_raises_attributeerror_due_to_li_tif_bug(self):
        """Document a pre-existing bug: rasters reference an undefined attribute.

        ``count_files_to_process`` queues rasters with
        ``list_of_datasets=self.li_tif``, but ``self.li_tif`` is never set
        anywhere in ``ProcessingFiles.__init__`` (the file-list attribute is
        named ``self.li_rasters``). As soon as ``opt_analyze_raster`` is True
        and ``li_rasters`` is non-empty, this raises ``AttributeError``
        instead of queueing the raster files. This test pins that behavior;
        if ``self.li_tif`` is corrected to ``self.li_rasters``, replace this
        test with one asserting the rasters are queued normally.
        """
        processor = _make_processor(li_rasters=["ortho.tif"])

        with self.assertRaises(AttributeError):
            processor.count_files_to_process()

    def test_cdao_files_get_unresolved_georeader_due_to_file_cad_key_mismatch(self):
        """Document a pre-existing bug: CAD/DAO files get no georeader.

        ``count_files_to_process`` queues CAD/DAO files with
        ``dataset_format="file_cad"``, but ``MATRIX_FORMAT_GEOREADER`` has no
        ``"file_cad"`` key (only ``"dxf"``). So every queued CAD/DAO dataset
        ends up with ``georeader=None``, and calling ``dataset.georeader()``
        later (as ``read_dataset`` does) would raise ``TypeError: 'NoneType'
        object is not callable``. This test pins that behavior; if the format
        key is corrected, update this test to assert a real georeader class
        is resolved instead.
        """
        processor = _make_processor(li_cdao=["plan.dxf"])

        processor.count_files_to_process()

        self.assertEqual(len(processor.li_files_to_process), 1)
        self.assertIsNone(processor.li_files_to_process[0].georeader)


# ############################################################################
# ####### Stand-alone run ########
# ################################
if __name__ == "__main__":
    unittest.main()
