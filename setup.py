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
        "Docs": __about__.__uri_doc__,
        "Bug Reports": "{}issues/".format(__about__.__uri__),
        "Source": __about__.__uri__,
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
        "dev": requirements_dev,
        "doc": requirements_docs,
    },
    install_requires=requirements,
    # run
    entry_points={
        "gui_scripts": [
            "dicogis = dicogis.DicoGIS:__main__",
        ]
    },
    # metadata
    keywords="GIS metadata INSPIRE GDAL",
    classifiers=[
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Information Technology",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: Implementation :: CPython",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Win32 (MS Windows)",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows :: Windows 10",
    ],
)
