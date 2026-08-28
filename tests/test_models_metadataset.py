#! python3  # noqa E265

"""
Usage from the repo root folder:

.. code-block:: bash
    # for whole tests
    python -m unittest tests.test_models_metadataset
    # for specific test
    python -m unittest tests.test_models_metadataset.TestPathAsStr.test_path_instance
"""

# standard library
import unittest
from pathlib import Path
from unittest.mock import patch

# project
from dicogis.models.database_connection import DatabaseConnection
from dicogis.models.feature_attributes import AttributeField
from dicogis.models.metadataset import (
    MetaDatabaseFlat,
    MetaDatabaseTable,
    MetaDataset,
    MetaRasterDataset,
    MetaVectorDataset,
)

# ############################################################################
# ########## Classes #############
# ################################


class TestPathAsStr(unittest.TestCase):
    """Test MetaDataset.path_as_str."""

    def test_path_instance_is_resolved(self):
        metadataset = MetaDataset(path=Path("data/parcels.shp"))

        self.assertEqual(
            metadataset.path_as_str, str(Path("data/parcels.shp").resolve())
        )

    def test_no_path_and_not_a_database_table_returns_none(self):
        metadataset = MetaDataset(path=None)

        self.assertIsNone(metadataset.path_as_str)

    @patch("dicogis.models.database_connection.pgserviceparser.service_names")
    def test_database_table_with_known_service_uses_pg_connection_uri(
        self, mock_service_names
    ):
        mock_service_names.return_value = ["srv_test"]
        metadataset = MetaDatabaseTable(
            database_connection=DatabaseConnection(service_name="srv_test")
        )

        self.assertEqual(metadataset.path_as_str, "postgresql://?service=srv_test")

    def test_database_table_without_service_builds_connection_string(self):
        metadataset = MetaDatabaseTable(
            database_connection=DatabaseConnection(
                service_name=None,
                user_name="alice",
                host="localhost",
                port=5432,
                database_name="gis",
            )
        )

        self.assertEqual(
            metadataset.path_as_str, "postgresql://alice@localhost:5432/gis"
        )


class TestSlug(unittest.TestCase):
    """Test MetaDataset.slug."""

    def test_vector_dataset_slug_includes_parent_folder_and_name(self):
        metadataset = MetaVectorDataset(
            name="Parcels", parent_folder_name="Data Folder"
        )

        self.assertEqual(metadataset.slug, "data-folder-parcels")

    def test_database_table_slug_includes_database_and_schema(self):
        metadataset = MetaDatabaseTable(
            name="Roads",
            schema_name="public",
            database_connection=DatabaseConnection(database_name="GIS DB"),
        )

        self.assertEqual(metadataset.slug, "gis-db-public-roads")

    def test_database_table_slug_falls_back_to_service_name(self):
        metadataset = MetaDatabaseTable(
            name="Roads",
            schema_name="public",
            database_connection=DatabaseConnection(
                database_name=None, service_name="srv_test"
            ),
        )

        self.assertEqual(metadataset.slug, "srv_test-public-roads")

    def test_plain_metadataset_slug_is_just_the_name(self):
        metadataset = MetaDataset(name="Just A Name")

        self.assertEqual(metadataset.slug, "just-a-name")


class TestSignature(unittest.TestCase):
    """Test MetaDataset.signature()."""

    def test_deterministic(self):
        metadataset = MetaDataset(name="parcels", crs_name="RGF93")

        self.assertEqual(metadataset.signature(), metadataset.signature())

    def test_different_name_changes_signature(self):
        metadataset_a = MetaDataset(name="parcels")
        metadataset_b = MetaDataset(name="buildings")

        self.assertNotEqual(metadataset_a.signature(), metadataset_b.signature())

    def test_known_bug_envelope_never_affects_signature(self):
        """Document a pre-existing bug: `envelope` is listed in
        hashable_attributes but is never actually hashed.

        The special-case branch for a tuple value only applies "when
        obj_attribute == 'feature_attributes'", so a tuple envelope value
        falls to the generic `else: hasher.update(hash(str(attr_value)...))`
        branch -- which always raises TypeError (hash() returns an int, not
        a bytes-like object) and is silently swallowed by the surrounding
        try/except. So two metadatasets with different envelopes but
        otherwise identical hashable attributes get the same signature.
        """
        metadataset_a = MetaDataset(name="parcels", envelope=(0.0, 0.0, 1.0, 1.0))
        metadataset_b = MetaDataset(name="parcels", envelope=(10.0, 10.0, 20.0, 20.0))

        self.assertEqual(metadataset_a.signature(), metadataset_b.signature())

    def test_known_bug_feature_attributes_list_never_affects_signature(self):
        """Document a pre-existing bug: feature_attributes (declared as
        list[AttributeField]) is listed in hashable_attributes, but the
        special per-item hashing branch only triggers for an actual tuple
        (`isinstance(attr_value, tuple)`) -- a real-world list value falls
        to the same broken `else` branch as above and is silently dropped.
        So two vector datasets with completely different field lists (but
        otherwise identical hashable attributes) get the same signature.
        """
        metadataset_a = MetaVectorDataset(
            name="parcels",
            feature_attributes=[AttributeField(name="id", data_type="Integer")],
        )
        metadataset_b = MetaVectorDataset(
            name="parcels",
            feature_attributes=[
                AttributeField(name="id", data_type="Integer"),
                AttributeField(name="area", data_type="Real"),
            ],
        )

        self.assertEqual(metadataset_a.signature(), metadataset_b.signature())

    def test_feature_attributes_as_an_actual_tuple_does_affect_signature(self):
        """The special per-item branch does work when feature_attributes is
        passed as a real tuple (not the declared list type)."""
        metadataset_a = MetaVectorDataset(
            name="parcels",
            feature_attributes=(AttributeField(name="id", data_type="Integer"),),
        )
        metadataset_b = MetaVectorDataset(
            name="parcels",
            feature_attributes=(AttributeField(name="area", data_type="Real"),),
        )

        self.assertNotEqual(metadataset_a.signature(), metadataset_b.signature())


class TestAsMarkdownDescription(unittest.TestCase):
    """Test MetaDataset.as_markdown_description."""

    def test_includes_dataset_type_and_format(self):
        metadataset = MetaDataset(
            dataset_type="flat_vector", format_gdal_long_name="ESRI Shapefile"
        )

        description = metadataset.as_markdown_description

        self.assertIn("flat_vector", description)
        self.assertIn("ESRI Shapefile", description)

    def test_vector_dataset_includes_feature_attributes_table(self):
        metadataset = MetaVectorDataset(
            geometry_type="Polygon",
            feature_attributes=[AttributeField(name="id", data_type="Integer")],
        )

        description = metadataset.as_markdown_description

        self.assertIn("Polygon", description)
        self.assertIn("Feature attributes", description)
        self.assertIn("| id |", description)

    def test_raster_dataset_includes_image_metadata(self):
        metadataset = MetaRasterDataset(
            bands_count=3, rows_count=100, columns_count=200
        )

        description = metadataset.as_markdown_description

        self.assertIn("Image metadata", description)
        self.assertIn("Bands count | 3", description)


class TestMetaVectorDataset(unittest.TestCase):
    """Test MetaVectorDataset properties."""

    def test_count_feature_attributes(self):
        metadataset = MetaVectorDataset(
            feature_attributes=[
                AttributeField(name="id"),
                AttributeField(name="label"),
            ]
        )

        self.assertEqual(metadataset.count_feature_attributes, 2)

    def test_count_feature_attributes_none_when_unset(self):
        metadataset = MetaVectorDataset(feature_attributes=None)

        self.assertIsNone(metadataset.count_feature_attributes)

    def test_as_markdown_feature_attributes_empty_when_unset(self):
        metadataset = MetaVectorDataset(feature_attributes=None)

        self.assertEqual(metadataset.as_markdown_feature_attributes, "")

    def test_as_markdown_feature_attributes_lists_every_field(self):
        metadataset = MetaVectorDataset(
            feature_attributes=[
                AttributeField(name="id", data_type="Integer", length=10, precision=0),
            ]
        )

        markdown = metadataset.as_markdown_feature_attributes

        self.assertIn("| id | Integer | 10 | 0 |", markdown)


class TestMetaDatabaseFlat(unittest.TestCase):
    """Test MetaDatabaseFlat properties."""

    def test_cumulated_counts_and_layer_count(self):
        metadataset = MetaDatabaseFlat(
            layers=[
                MetaVectorDataset(
                    feature_attributes=[AttributeField(name="id")],
                    features_objects_count=5,
                ),
                MetaVectorDataset(
                    feature_attributes=[
                        AttributeField(name="id"),
                        AttributeField(name="label"),
                    ],
                    features_objects_count=9,
                ),
            ]
        )

        self.assertEqual(metadataset.count_layers, 2)
        self.assertEqual(metadataset.cumulated_count_feature_attributes, 3)
        self.assertEqual(metadataset.cumulated_count_feature_objects, 14)

    def test_none_layers_returns_none_for_every_property(self):
        metadataset = MetaDatabaseFlat(layers=None)

        self.assertIsNone(metadataset.count_layers)
        self.assertIsNone(metadataset.cumulated_count_feature_attributes)
        self.assertIsNone(metadataset.cumulated_count_feature_objects)


# ############################################################################
# ####### Stand-alone run ########
# ################################
if __name__ == "__main__":
    unittest.main()
