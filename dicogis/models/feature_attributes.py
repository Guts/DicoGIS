#! python3  # noqa: E265

"""
    Feature attribute model.
"""

# ############################################################################
# ######### Libraries #############
# #################################

# Standard library
from __future__ import (
    annotations,  # used to manage type annotation for method that return Self in Python < 3.11
)

import logging
from dataclasses import dataclass
from hashlib import sha256

# ############################################################################
# ########## Globals ###############
# ##################################


logger = logging.getLogger(__name__)

# ############################################################################
# ######### Classes #############
# ###############################


@dataclass
class AttributeField:
    """Feature attribute (field) abstraction model."""

    name: str
    alias: str | None = None
    data_type: str | None = None
    description: str | None = None
    length: int | None = None
    precision: float | None = None
    text_language: str | None = None

    @property
    def signature(self) -> str:
        """Calculate a hash cumulating certain attributes values.

        Returns:
            object hexdigest
        """

        hasher = sha256(usedforsecurity=False)
        hashable_attributes: tuple = ("name", "data_type", "length", "precision")
        # parse attributes
        for obj_attribute in hashable_attributes:
            # because hash.update requires a
            if attr_value := getattr(self, obj_attribute, None):
                try:
                    if isinstance(attr_value, str):
                        hasher.update(attr_value.encode())
                    elif isinstance(attr_value, (float, int)):
                        hasher.update(str(attr_value).encode())
                    else:
                        hasher.update(hash(str(attr_value).encode()))
                except TypeError as err:
                    logger.info(
                        f"Impossible to hash {obj_attribute} value "
                        f"({attr_value, type(attr_value)}). Trace: {err}"
                    )

        return hasher.hexdigest()
