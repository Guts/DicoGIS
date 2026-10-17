#! python3  # noqa: E265

"""Path helpers pathlib doesn't provide."""

# ############################################################################
# ########## Libraries #############
# ##################################

# standard lib
from os.path import abspath
from pathlib import Path


# ############################################################################
# ########## Functions #############
# ##################################


def absolute_path(input_path: Path | str) -> Path:
    """Make a path absolute and lexically normalized, without touching the disk.

    pathlib has no exact equivalent: Path.absolute() keeps ".." components, and
    Path.resolve() also follows symbolic links and, on Windows, expands 8.3
    short names (e.g. RUNNER~1), which changes paths compared or displayed
    elsewhere. This is the one place where os.path is used on purpose.

    Args:
        input_path: path to make absolute, relative to the current directory

    Returns:
        absolute path, with "." and ".." components collapsed
    """
    return Path(abspath(input_path))  # noqa: PTH100 - see docstring
