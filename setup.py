#! python3  # noqa: E265

# ############################################################################
# ########## Libraries #############
# ##################################

# standard library
import pathlib

# 3rd party
from setuptools import find_packages, setup

# package (to get version)
from dicogis import __about__

# ############################################################################
# ########## Globals #############
# ##############################

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

# ############################################################################
# ########## Setup #############
# ##############################

setup(
    name="dicogis",
    version=__about__.__version__,
    author=__about__.__author__,
    author_email=__about__.__email__,
    description=__about__.__summary__,
    license="GPL3",
    long_description=README,
    long_description_content_type="text/markdown",
    url=__about__.__uri__,
    project_urls={
        "Bug Reports": "{}issues/".format(__about__.__uri__),
        "Source": __about__.__uri__,
    },
    py_modules=["dicogis"],
    # packaging
    # packages=find_packages(
    #     exclude=["contrib", "docs", "*.tests", "*.tests.*", "tests.*", "tests"]
    # ),
    include_package_data=True,
    # dependencies
    python_requires=">=3.8, <4",
    install_requires=[
        "dxfgrabber>=1.0,<1.1",
        # "gdal>=3,<4" ,
        "geoserver-restconfig>=2.0.4,<2.0.5",
        "numpy>=1.22,<1.23",
        "openpyxl>=3.0,<3.1",
        "xmltodict>=0.12,<1",
    ],
    setup_requires=["openpyxl>=3.0,<3.1"],
    # metadata
    classifiers=[
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Information Technology",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: CPython",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Win32 (MS Windows)",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows :: Windows 10",
    ],
)
