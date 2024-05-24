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

from dataclasses import dataclass

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
