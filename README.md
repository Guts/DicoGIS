# DicoGIS

[![Build 📦 and release 🚀](https://github.com/Guts/DicoGIS/actions/workflows/builder_releaser.yml/badge.svg)](https://github.com/Guts/DicoGIS/actions/workflows/builder_releaser.yml)
[![Linter 🐍](https://github.com/Guts/DicoGIS/actions/workflows/linter_ubuntu.yml/badge.svg)](https://github.com/Guts/DicoGIS/actions/workflows/linter_ubuntu.yml)
[![Tester 🎳](https://github.com/Guts/DicoGIS/actions/workflows/tester_ubuntu.yml/badge.svg)](https://github.com/Guts/DicoGIS/actions/workflows/tester_ubuntu.yml)
[![📚 Documentation Builder](https://github.com/Guts/DicoGIS/actions/workflows/docs_builder.yml/badge.svg)](https://github.com/Guts/DicoGIS/actions/workflows/docs_builder.yml)
[![codecov](https://codecov.io/gh/Guts/DicoGIS/branch/master/graph/badge.svg?token=phiBV8BfPA)](https://codecov.io/gh/Guts/DicoGIS)

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/Guts/DicoGIS/master.svg)](https://results.pre-commit.ci/latest/github/Guts/DicoGIS/master)

![GitHub all releases](https://img.shields.io/github/downloads/guts/dicogis/total)

Automatize the creation of a dictionnary of geographic data in a folders structure. The output dictionary is an Excel file (.xlsx).

For further information, see [the documentation](https://guts.github.io/DicoGIS/).

## Installation

DicoGIS relies on GDAL, declared as an optional dependency so that
`pipx install dicogis` (or `pip install dicogis`) always succeeds, even
without GDAL. Getting GDAL into a pipx-managed virtual environment needs a
couple of extra steps depending on your OS — see the
[pipx installation guide](https://guts.github.io/DicoGIS/usage/installation.html).

PyQt6, needed only for the `dicogis-gui` desktop app, is likewise an optional
dependency (the `gui` extra): `pip install dicogis[gui]` /
`pipx inject dicogis PyQt6`. `dicogis-cli` never needs it.

If you'd rather avoid Python/GDAL packaging altogether, standalone CLI/GUI
executables (Windows and Ubuntu) that embed GDAL are published on the
[latest release](https://github.com/Guts/DicoGIS/releases/latest).
