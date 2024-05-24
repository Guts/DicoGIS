#! python3  # noqa: E265

"""Helpers to format text and variables."""


# standard library
import logging
from functools import lru_cache
from math import floor
from math import log as math_log

# ############################################################################
# ########## GLOBALS #############
# ################################

logger = logging.getLogger(__name__)


# ############################################################################
# ########## FUNCTIONS ###########
# ################################


@lru_cache(maxsize=512)
def convert_octets(octets: int) -> str:
    """Convert a mount of octets in readable size.

    Args:
        octets: mount of octets to convert

    Returns:
        size in a human readable format: ko, Mo, etc.

    Example:

    .. code-block:: python

        >>> convert_octets(1024)
        1 ko
        >>> from pathlib import Path
        >>> convert_octets(Path(my_file.txt).stat().st_size)
    """
    # check zero
    if octets == 0:
        return "0 octet"

    # conversion
    size_name = ("octets", "Ko", "Mo", "Go", "To", "Po")
    i = int(floor(math_log(octets, 1024)))
    p = pow(1024, i)
    s = round(octets / p, 2)

    return f"{s} {size_name[i]}"


def secure_encoding(layer_dict: dict, key_str: str) -> str:
    """Check if dictionary value is compatible with XML encoding.

    Args:
        layer_dict (dict): layer metadata dictionary
        key_str (str): key fo dictionary to check

    Returns:
        str: clean string
    """
    try:
        out_str = layer_dict.get(key_str, "").encode("utf-8", "strict")
        return out_str
    except UnicodeError as err:
        err_msg = "Encoding error spotted in '{}' for layer {}".format(
            key_str, layer_dict.get("name")
        )
        logger.warning(
            "{}. Layer: {}. Trace: {}".format(err_msg, layer_dict.get("name"), err)
        )
        return layer_dict.get(key_str, "").encode("utf8", "xmlcharrefreplace")
