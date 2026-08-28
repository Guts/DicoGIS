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

    def test_known_bug_datetime_silently_becomes_none(self):
        """Document current behavior: dates vanish instead of being encoded.

        ``json_encoder_for_unsupported_types`` only special-cases
        ``pathlib.Path``; any other type (e.g. ``datetime``, used for
        ``storage_date_created``/``storage_date_updated``) falls through
        with no ``return`` statement, implicitly returning ``None``. Since
        ``json.dump``'s ``default`` callback is expected to return a
        JSON-serializable substitute (or raise), this silently serializes
        every date field as ``null`` instead of e.g. an ISO string. This
        test pins that behavior; if the encoder is extended to handle
        datetimes, update this test to assert an ISO-formatted string
        instead.
        """
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdirname:
            serializer = _make_serializer(output_path=Path(tmpdirname))

            result = serializer.json_encoder_for_unsupported_types(datetime(2024, 1, 1))

            self.assertIsNone(result)


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

    def test_known_bug_output_path_none_raises_attributeerror(self):
        """Document current behavior: output_path is not actually optional.

        The signature advertises ``output_path: Path | None = None``, but
        ``__init__`` immediately calls ``output_path.mkdir(...)`` before
        ever delegating to the base class -- so constructing without an
        explicit ``output_path`` raises ``AttributeError: 'NoneType' object
        has no attribute 'mkdir'`` instead of behaving like
        ``MetadatasetSerializerXlsx``, where ``output_path`` is genuinely
        optional until ``post_serializing()`` is called.
        """
        with self.assertRaises(AttributeError):
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

    def test_known_bug_dates_are_serialized_as_null(self):
        """Document current behavior: created/updated dates vanish in JSON.

        Because ``json_encoder_for_unsupported_types`` doesn't handle
        ``datetime`` (see ``TestJsonEncoderForUnsupportedTypes``), a
        metadataset with real creation/update dates loses that information
        entirely when serialized with the "dicogis" flavor: both fields
        come back as JSON ``null``.
        """
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
            self.assertIsNone(content["storage_date_created"])
            self.assertIsNone(content["storage_date_updated"])

    def test_known_bug_unsupported_flavor_silently_writes_empty_file(self):
        """Document current behavior: an unrecognized flavor writes nothing.

        ``serialize_metadaset`` only handles ``self.flavor in ("dicogis",
        "udata")``; any other value (bypassing the type hint, e.g. set
        directly on the instance) falls through both branches with no
        ``else``, leaving the opened output file empty -- no error is
        raised, so the caller has no way to know serialization silently
        did nothing.
        """
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdirname:
            serializer = _make_serializer(output_path=Path(tmpdirname))
            serializer.flavor = "not-a-real-flavor"
            metadataset = MetaDataset(name="parcels")

            output_file = serializer.serialize_metadaset(metadataset=metadataset)

            self.assertTrue(output_file.is_file())
            self.assertEqual(output_file.read_text(encoding="UTF-8"), "")

    def test_known_bug_unnamed_metadataset_crashes(self):
        """Document current behavior: name=None (the dataclass default)
        crashes serialize_metadaset instead of e.g. falling back to a
        generated filename.

        ``serialize_metadaset`` slugifies ``metadataset.name`` directly via
        ``sluggy()``, which requires a string; passing ``None`` raises
        ``TypeError`` from within ``unicodedata``/regex processing.
        """
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdirname:
            serializer = _make_serializer(output_path=Path(tmpdirname))
            metadataset = MetaDataset(name=None)

            with self.assertRaises(TypeError):
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
