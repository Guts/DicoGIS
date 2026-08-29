#! python3  # noqa E265

"""
Usage from the repo root folder:

.. code-block:: bash
    # for whole tests
    python -m unittest tests.test_models_feature_attributes
    # for specific test
    python -m unittest tests.test_models_feature_attributes.TestAttributeFieldSignature.test_deterministic
"""

# standard library
import unittest

# project
from dicogis.models.feature_attributes import AttributeField

# ############################################################################
# ########## Classes #############
# ################################


class TestAttributeFieldSignature(unittest.TestCase):
    """Test AttributeField.signature()."""

    def test_deterministic(self):
        field = AttributeField(name="id", data_type="Integer", length=10, precision=0)

        self.assertEqual(field.signature, field.signature)

    def test_is_a_valid_sha256_hexdigest(self):
        field = AttributeField(name="id", data_type="Integer")

        signature = field.signature

        self.assertEqual(len(signature), 64)
        int(signature, 16)  # raises ValueError if not valid hex

    def test_different_name_changes_signature(self):
        field_a = AttributeField(name="id")
        field_b = AttributeField(name="other")

        self.assertNotEqual(field_a.signature, field_b.signature)

    def test_different_data_type_changes_signature(self):
        field_a = AttributeField(name="id", data_type="Integer")
        field_b = AttributeField(name="id", data_type="String")

        self.assertNotEqual(field_a.signature, field_b.signature)

    def test_different_length_changes_signature(self):
        field_a = AttributeField(name="label", length=50)
        field_b = AttributeField(name="label", length=100)

        self.assertNotEqual(field_a.signature, field_b.signature)

    def test_alias_description_and_language_do_not_affect_signature(self):
        """Only name/data_type/length/precision are hashed -- alias,
        description and text_language are intentionally excluded."""
        field_a = AttributeField(
            name="id", alias="ID", description="primary key", text_language="en"
        )
        field_b = AttributeField(
            name="id", alias="Other alias", description="other", text_language="fr"
        )

        self.assertEqual(field_a.signature, field_b.signature)

    def test_explicit_zero_length_differs_from_unset(self):
        """A field with an explicit zero length is now distinguishable from
        one where length was never set (previously both were skipped from
        the hash, since the field is checked for truthiness rather than
        for being not-None)."""
        field_zero = AttributeField(name="flag", length=0)
        field_unset = AttributeField(name="flag", length=None)

        self.assertNotEqual(field_zero.signature, field_unset.signature)


# ############################################################################
# ####### Stand-alone run ########
# ################################
if __name__ == "__main__":
    unittest.main()
