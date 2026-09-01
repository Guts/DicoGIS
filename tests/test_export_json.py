#! python3  # noqa E265

"""
Usage from the repo root folder:

.. code-block:: bash
    # for whole tests
    python -m unittest tests.test_export_json
    # for specific test
    python -m unittest tests.test_export_json.TestAsUdata.test_basic_shape
"""

# standard library
import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

# project
from dicogis.export.base_serializer import MetadatasetSerializerBase
from dicogis.export.to_json import MetadatasetSerializerJson
from dicogis.export.to_xlsx import MetadatasetSerializerXlsx
from dicogis.models.metadataset import MetaDataset


# ############################################################################
# ########## Globals #############
# ################################


def _make_serializer(output_path: Path, **overrides) -> MetadatasetSerializerJson:
    kwargs = dict(localized_strings={}, output_path=output_path)
    kwargs.update(overrides)
    return MetadatasetSerializerJson(**kwargs)


# ############################################################################
# ########## Classes #############
# ################################


class TestJsonEncoderForUnsupportedTypes(unittest.TestCase):
    """Test MetadatasetSerializerJson.json_encoder_for_unsupported_types()."""

    def test_path_is_stringified(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdirname:
            serializer = _make_serializer(output_path=Path(tmpdirname))

            result = serializer.json_encoder_for_unsupported_types(Path("a/b.shp"))

            self.assertEqual(result, str(Path("a/b.shp")))

    def test_datetime_is_isoformatted(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdirname:
            serializer = _make_serializer(output_path=Path(tmpdirname))

            result = serializer.json_encoder_for_unsupported_types(datetime(2024, 1, 1))

            self.assertEqual(result, datetime(2024, 1, 1).isoformat())

    def test_set_is_sorted_into_a_list(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdirname:
            serializer = _make_serializer(output_path=Path(tmpdirname))

            result = serializer.json_encoder_for_unsupported_types({"b", "a", "c"})

            self.assertEqual(result, ["a", "b", "c"])

    def test_truly_unsupported_type_raises_typeerror(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdirname:
            serializer = _make_serializer(output_path=Path(tmpdirname))

            with self.assertRaises(TypeError):
                serializer.json_encoder_for_unsupported_types(object())


class TestMetadatasetSerializerJsonInit(unittest.TestCase):
    """Test MetadatasetSerializerJson.__init__()."""

    def test_output_folder_is_created(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdirname:
            output_path = Path(tmpdirname) / "nested" / "output"

            _make_serializer(output_path=output_path)

            self.assertTrue(output_path.is_dir())

    def test_default_flavor_is_dicogis(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdirname:
            serializer = _make_serializer(output_path=Path(tmpdirname))

            self.assertEqual(serializer.flavor, "dicogis")

    def test_output_path_none_raises_clear_valueerror(self):
        """output_path is required (unlike MetadatasetSerializerXlsx, where
        it's genuinely optional until post_serializing()); missing it raises
        a clear ValueError instead of an obscure AttributeError."""
        with self.assertRaises(ValueError):
            MetadatasetSerializerJson(localized_strings={})


class TestAsUdata(unittest.TestCase):
    """Test MetadatasetSerializerJson.as_udata()."""

    def _metadataset(self, **overrides) -> MetaDataset:
        kwargs = dict(
            name="parcels",
            path=Path("data/parcels.shp"),
            format_gdal_long_name="ESRI Shapefile",
            format_gdal_short_name="ESRI Shapefile",
            crs_name="RGF93",
        )
        kwargs.update(overrides)
        return MetaDataset(**kwargs)

    def test_basic_shape(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdirname:
            serializer = _make_serializer(output_path=Path(tmpdirname))
            metadataset = self._metadataset()

            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("DICOGIS_UDATA_ORGANIZATION_ID", None)
                result = serializer.as_udata(metadataset)

            self.assertEqual(result["title"], "parcels")
            self.assertIn("dicogis_original_path", result["extras"])
            self.assertIn("dicogis_signature", result["extras"])
            self.assertIn("ESRI Shapefile", result["tags"])
            self.assertNotIn("organization", result)

    def test_crs_undefined_fallback(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdirname:
            serializer = _make_serializer(output_path=Path(tmpdirname))
            metadataset = self._metadataset(crs_name=None)

            result = serializer.as_udata(metadataset)

            self.assertIn("srs_undefined", result["tags"])

    def test_organization_added_from_environment_variable(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdirname:
            serializer = _make_serializer(output_path=Path(tmpdirname))
            metadataset = self._metadataset()

            with patch.dict("os.environ", {"DICOGIS_UDATA_ORGANIZATION_ID": "org-123"}):
                result = serializer.as_udata(metadataset)

            self.assertEqual(result["organization"], "org-123")


class TestSerializeMetadataset(unittest.TestCase):
    """Test MetadatasetSerializerJson.serialize_metadaset()."""

    def test_dicogis_flavor_writes_full_metadataset_as_json(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdirname:
            serializer = _make_serializer(
                output_path=Path(tmpdirname), flavor="dicogis"
            )
            metadataset = MetaDataset(name="parcels", format_gdal_long_name="GML")

            output_file = serializer.serialize_metadaset(metadataset=metadataset)

            self.assertTrue(output_file.is_file())
            with output_file.open(encoding="UTF-8") as f:
                content = json.load(f)
            self.assertEqual(content["name"], "parcels")
            self.assertEqual(content["format_gdal_long_name"], "GML")

    def test_udata_flavor_writes_as_udata_shape(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdirname:
            serializer = _make_serializer(output_path=Path(tmpdirname), flavor="udata")
            metadataset = MetaDataset(name="parcels", format_gdal_long_name="GML")

            output_file = serializer.serialize_metadaset(metadataset=metadataset)

            with output_file.open(encoding="UTF-8") as f:
                content = json.load(f)
            self.assertEqual(content["title"], "parcels")
            self.assertIn("extras", content)

    def test_filename_is_slugified_dataset_name(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdirname:
            serializer = _make_serializer(output_path=Path(tmpdirname))
            metadataset = MetaDataset(name="Parcelles Communales !")

            output_file = serializer.serialize_metadaset(metadataset=metadataset)

            self.assertEqual(output_file.name, "parcelles-communales.json")

    def test_dates_are_isoformatted(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdirname:
            serializer = _make_serializer(output_path=Path(tmpdirname))
            metadataset = MetaDataset(
                name="parcels",
                storage_date_created=datetime(2024, 1, 1),
                storage_date_updated=datetime(2024, 6, 1),
            )

            output_file = serializer.serialize_metadaset(metadataset=metadataset)

            with output_file.open(encoding="UTF-8") as f:
                content = json.load(f)
            self.assertEqual(
                content["storage_date_created"], datetime(2024, 1, 1).isoformat()
            )
            self.assertEqual(
                content["storage_date_updated"], datetime(2024, 6, 1).isoformat()
            )

    def test_unsupported_flavor_raises_valueerror_without_writing_a_file(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdirname:
            serializer = _make_serializer(output_path=Path(tmpdirname))
            serializer.flavor = "not-a-real-flavor"
            metadataset = MetaDataset(name="parcels")

            with self.assertRaises(ValueError):
                serializer.serialize_metadaset(metadataset=metadataset)

            self.assertEqual(list(Path(tmpdirname).iterdir()), [])

    def test_unnamed_metadataset_raises_clear_valueerror(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdirname:
            serializer = _make_serializer(output_path=Path(tmpdirname))
            metadataset = MetaDataset(name=None)

            with self.assertRaises(ValueError):
                serializer.serialize_metadaset(metadataset=metadataset)


class TestGetSerializerFromParameters(unittest.TestCase):
    """Test MetadatasetSerializerBase.get_serializer_from_parameters()."""

    def test_passthrough_existing_serializer_instance(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdirname:
            existing = _make_serializer(output_path=Path(tmpdirname))

            result = MetadatasetSerializerBase.get_serializer_from_parameters(
                format_or_serializer=existing
            )

            self.assertIs(result, existing)

    def test_excel_string_returns_xlsx_serializer(self):
        result = MetadatasetSerializerBase.get_serializer_from_parameters(
            format_or_serializer="excel", localized_strings={}
        )

        self.assertIsInstance(result, MetadatasetSerializerXlsx)

    def test_json_string_returns_dicogis_flavored_json_serializer(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdirname:
            result = MetadatasetSerializerBase.get_serializer_from_parameters(
                format_or_serializer="json",
                output_path=Path(tmpdirname),
                localized_strings={},
            )

            self.assertIsInstance(result, MetadatasetSerializerJson)
            self.assertEqual(result.flavor, "dicogis")

    def test_udata_string_returns_udata_flavored_json_serializer(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdirname:
            result = MetadatasetSerializerBase.get_serializer_from_parameters(
                format_or_serializer="udata",
                output_path=Path(tmpdirname),
                localized_strings={},
            )

            self.assertIsInstance(result, MetadatasetSerializerJson)
            self.assertEqual(result.flavor, "udata")

    def test_invalid_string_raises_valueerror(self):
        with self.assertRaises(ValueError):
            MetadatasetSerializerBase.get_serializer_from_parameters(
                format_or_serializer="bogus-format"
            )

    def test_known_gap_non_string_non_enum_raises_notimplementederror(self):
        """A value that is neither a str, a serializer instance, nor equal
        to any OutputFormats member falls through every branch straight to
        the final ``else: raise NotImplementedError`` -- reachable only
        via a type the string-conversion step can't intercept, e.g. a bare
        int.
        """
        with self.assertRaises(NotImplementedError):
            MetadatasetSerializerBase.get_serializer_from_parameters(
                format_or_serializer=42
            )


# ############################################################################
# ####### Stand-alone run ########
# ################################
if __name__ == "__main__":
    unittest.main()
