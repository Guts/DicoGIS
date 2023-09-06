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


with open(HERE / "requirements/base.txt") as f:
    requirements = [
        line
        for line in f.read().splitlines()
        if not line.startswith(("#", "-")) and len(line)
    ]

with open(HERE / "requirements/development.txt") as f:
    requirements_dev = [
        line
        for line in f.read().splitlines()
        if not line.startswith(("#", "-")) and len(line)
    ]


with open(HERE / "requirements/documentation.txt") as f:
    requirements_docs = [
        line
        for line in f.read().splitlines()
        if not line.startswith(("#", "-")) and len(line)
    ]

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
    license="GPL3",
    long_description=(HERE / "README.md").read_text(),
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
    python_requires=">=3.9, <4",
    extras_require={
        "dev": load_requirements(HERE / "requirements/development.txt"),
        "doc": load_requirements(HERE / "requirements/documentation.txt"),
        "test": load_requirements(HERE / "requirements/testing.txt"),
        "gdal": f"gdal=={get_gdal_version()}",
    },
    install_requires=load_requirements(HERE / "requirements/base.txt"),
    # run
    entry_points={
        "gui_scripts": [
            "dicogis = dicogis.DicoGIS:__main__",
        ]
    },
    # metadata
    keywords=__about__.__keywords__,
    classifiers=[
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Information Technology",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: Implementation :: CPython",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Win32 (MS Windows)",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows :: Windows 10",
        "Topic :: Scientific/Engineering :: GIS",
    ],
)
