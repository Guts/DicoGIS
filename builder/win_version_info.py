#! python3  # noqa: E265

"""
Windows version resource of the executables, built from the package metadata.

PyInstaller's `--version-file` only takes a file, which it reads back into a
`VSVersionInfo` structure: this module builds that structure from
`dicogis.__about__` and writes its text serialization for the build scripts.

Windows only: PyInstaller's version info classes need pywin32 and pefile.

See:

    - https://learn.microsoft.com/windows/win32/menurc/versioninfo-resource
    - https://learn.microsoft.com/windows/win32/api/verrsrc/ns-verrsrc-vs_fixedfileinfo
"""

# #############################################################################
# ########## Libraries #############
# ##################################

# Standard library
from pathlib import Path

# 3rd party
from PyInstaller.utils.win32.versioninfo import (
    FixedFileInfo,
    StringFileInfo,
    StringStruct,
    StringTable,
    VarFileInfo,
    VarStruct,
    VSVersionInfo,
)

# package
from dicogis import __about__


# #############################################################################
# ########### Functions ############
# ##################################


def build_version_info(executable_name: str) -> VSVersionInfo:
    """Build the version resource of an executable from the package metadata.

    Args:
        executable_name: file name of the executable, e.g. `DicoGIS-cli.exe`

    Returns:
        the version resource, as PyInstaller expects it
    """
    # Windows wants 4 integers: major, minor, patch, then 0 for pre-releases too
    # (4.0.0-beta12 -> 4.0.0.0), the full version being in the string fields
    version_tuple = (*__about__.__version_info__[:3], 0)

    return VSVersionInfo(
        ffi=FixedFileInfo(
            filevers=version_tuple,
            prodvers=version_tuple,
            # VS_FF_* flags: all valid, none set (not a debug or pre-release build)
            mask=0x3F,
            flags=0x0,
            # VOS_NT_WINDOWS32
            OS=0x40004,
            # VFT_APP
            fileType=0x1,
            subtype=0x0,
            date=(0, 0),
        ),
        kids=[
            StringFileInfo(
                [
                    # US English, Unicode: matches VarFileInfo's translation below
                    StringTable(
                        "040904B0",
                        [
                            StringStruct("CompanyName", __about__.__author__),
                            StringStruct("FileDescription", __about__.__summary__),
                            StringStruct("FileVersion", __about__.__version__),
                            StringStruct("InternalName", executable_name),
                            StringStruct("LegalCopyright", __about__.__copyright__),
                            StringStruct("OriginalFilename", executable_name),
                            StringStruct("ProductName", __about__.__title__),
                            StringStruct("ProductVersion", __about__.__version__),
                        ],
                    )
                ]
            ),
            VarFileInfo([VarStruct("Translation", [0x0409, 0x04B0])]),
        ],
    )


def write_version_info(executable_name: str, output_folder: Path) -> Path:
    """Write the version resource of an executable for PyInstaller's --version-file.

    Args:
        executable_name: file name of the executable, e.g. `DicoGIS-cli.exe`
        output_folder: folder where to write the file, created if needed

    Returns:
        path to the written file
    """
    output_folder.mkdir(parents=True, exist_ok=True)
    version_file = output_folder / f"{Path(executable_name).stem}_version_info.txt"
    version_file.write_text(str(build_version_info(executable_name)), encoding="UTF-8")
    return version_file
