#! python3  # noqa: E265

# ############################################################################
# ########## Libraries #############
# ##################################

# standard library
from pathlib import Path

# 3rd party
from setuptools import find_packages, setup

# package (to get version)
from dicogis import __about__
from dicogis.utils.environment import get_gdal_version

# ############################################################################
# ########## Globals #############
# ##############################

HERE = Path(__file__).parent


# ############################################################################
# ########### Functions ############
# ##################################


def load_requirements(requirements_files: Path | list[Path]) -> list:
    """Helper to load requirements list from a path or a list of paths.

    Args:
        requirements_files (Path | list[Path]): path or list to paths of requirements
            file(s)

    Returns:
        list: list of requirements loaded from file(s)
    """
    out_requirements = []

    if isinstance(requirements_files, Path):
        requirements_files = [
            requirements_files,
        ]

    for requirements_file in requirements_files:
        with requirements_file.open(encoding="UTF-8") as f:
            out_requirements += [
                line
                for line in f.read().splitlines()
                if not line.startswith(("#", "-")) and len(line)
            ]

    return out_requirements


# ############################################################################
# ########## Setup #############
# ##############################

setup(
    name=__about__.__package_name__,
    version=__about__.__version__,
    author=__about__.__author__,
    author_email=__about__.__email__,
    description=__about__.__summary__,
    license=__about__.__license__,
    long_description=(HERE / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    url=__about__.__uri__,
    project_urls={
        "Docs": __about__.__uri_homepage__,
        "Bug Reports": __about__.__uri_tracker__,
        "Source": __about__.__uri_repository__,
    },
    py_modules=["dicogis"],
    # packaging
    packages=find_packages(
        exclude=["contrib", "docs", "*.tests", "*.tests.*", "tests.*", "tests"]
    ),
    include_package_data=True,
    # dependencies
    python_requires=">=3.10, <4",
    extras_require={
        "dev": load_requirements(HERE / "requirements/development.txt"),
        "doc": load_requirements(HERE / "requirements/documentation.txt"),
        "test": load_requirements(HERE / "requirements/testing.txt"),
        "gdal": f"gdal=={get_gdal_version()}",
    },
    install_requires=load_requirements(HERE / "requirements/base.txt"),
    # run
    entry_points={
        "console_scripts": [
            f"{__about__.__package_name__}-cli = dicogis.cli.main:dicogis_cli"
        ],
        "gui_scripts": [
            f"{__about__.__package_name__}-gui = dicogis.ui.main:dicogis_gui",
        ],
    },
    # metadata
    keywords=__about__.__keywords__,
    classifiers=[
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Information Technology",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: Implementation :: CPython",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Win32 (MS Windows)",
        "License :: OSI Approved :: Apache Software License 2.0",
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows :: Windows 10",
        "Operating System :: Microsoft :: Windows :: Windows 11",
        "Topic :: Scientific/Engineering :: GIS",
    ],
)
