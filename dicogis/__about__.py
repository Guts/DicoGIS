#! python3  # noqa: E265

"""
Metadata about the package to easily retrieve informations about it.

See: https://packaging.python.org/guides/single-sourcing-package-version/
"""

# standard lib
from datetime import date
from pathlib import Path

__all__ = [
    "__author__",
    "__copyright__",
    "__email__",
    "__executable_name__",
    "__license__",
    "__summary__",
    "__title__",
    "__title_clean__",
    "__uri__",
    "__version__",
    "__version_info__",
]

__author__ = "Julien Moura"
__copyright__ = f"2014 - {date.today().year}, {__author__}"
__email__ = "dev@ingeoveritas.com"
__executable_name__ = "DicoGIS.exe"
__package_name__ = "dicogis"
__icon_path__ = Path("bin/img/DicoGIS_logo_200px.png")
__keywords__ = ["GIS", "metadata", "INSPIRE", "GDAL", "OGR", "data management"]
__license__ = "Apache-2.0"
__notification_sound_path__ = Path("bin/audio/notification_sound_microwave_bell.wav")
__summary__ = (
    "Create Excel spreadsheet describing geographical data from a PostGIS "
    "Database or a file tree structure."
)
__title__ = "DicoGIS"
__title_clean__ = "".join(e for e in __title__ if e.isalnum())
__uri_homepage__ = "https://guts.github.io/DicoGIS/"
__uri_repository__ = "https://github.com/Guts/DicoGIS/"
__uri_tracker__ = f"{__uri_repository__}issues/"
__uri__ = __uri_repository__


__version__ = "4.0.0-beta9"
__version_info__ = tuple(
    [
        int(num) if num.isdigit() else num
        for num in __version__.replace("-", ".", 1).split(".")
    ]
)
