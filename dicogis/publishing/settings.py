#! python3  # noqa: E265

"""Settings shared by the publishers."""

# ##############################################################################
# ########## Libraries #############
# ##################################

# standard lib
import logging
from os import getenv


# ##############################################################################
# ########## Globals ###############
# ##################################

logger = logging.getLogger(__name__)

DEFAULT_PUBLISH_TIMEOUT: float = 30.0

# ##############################################################################
# ########## Functions #############
# ##################################


def get_publish_timeout() -> float:
    """Read how long to wait for a catalog, in seconds.

    Returns:
        value of the DICOGIS_PUBLISH_TIMEOUT environment variable, or the default one
        if it's unset or isn't a positive number
    """
    value = getenv("DICOGIS_PUBLISH_TIMEOUT")
    if not value:
        return DEFAULT_PUBLISH_TIMEOUT
    try:
        timeout = float(value)
    except ValueError:
        timeout = 0.0
    if timeout <= 0:
        logger.warning(
            f"Invalid DICOGIS_PUBLISH_TIMEOUT value: '{value}'. "
            f"Using the default one: {DEFAULT_PUBLISH_TIMEOUT}."
        )
        return DEFAULT_PUBLISH_TIMEOUT
    return timeout
