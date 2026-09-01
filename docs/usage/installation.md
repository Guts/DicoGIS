# Installation with pipx

[pipx](https://pipx.pypa.io/) installs a Python CLI application into its own
isolated virtual environment while exposing its commands globally. It's a
convenient way to install `dicogis-cli` (or `dicogis-gui`) without polluting
your system Python or manually managing a virtual environment.

```sh
python -m pip install --user pipx
pipx ensurepath
```

## The GDAL challenge

DicoGIS relies on [GDAL](https://gdal.org/)/OGR to read geospatial datasets.
GDAL is declared as an **optional** dependency (the `gdal` extra in
`pyproject.toml`), so `pipx install dicogis` always succeeds and
`dicogis-cli --help` / `dicogis-cli --version` always work — but any command
that actually reads data (`dicogis-cli inventory`, `dicogis-gui`) will refuse
to run and tell you GDAL is missing.

The reason GDAL can't just be a normal dependency is that the `gdal` Python
package on PyPI is not a portable wheel: it must match the version of the
`libgdal` system library it links against (`gdal-config --version`), which
pip cannot resolve on its own inside an isolated pipx venv. You need to get a
matching GDAL into that venv yourself, using one of the options below.

## Prebuilt wheels, any platform

[Geospatial Wheels Index](https://geospatial-wheels-index.readthedocs.io/en/latest/)
publishes prebuilt GDAL wheels behind a package index, so pip can resolve and
install them like any other package: no manual `.whl` download and no
compilation against `libgdal-dev`.

On Linux, the wheel still links against the system `libgdal` (install it first,
see below), so the version has to be pinned to it:

```sh
python -m pip install --index-url https://gisidx.github.io/gwi gdal=="$(gdal-config --version).*"
```

On Windows, where there is no system GDAL to match, the version can be left to
pip:

```powershell
python -m pip install --index-url https://gisidx.github.io/gwi gdal
```

Within a DicoGIS installed through pipx (Linux form shown):

```sh
pipx install dicogis
pipx inject dicogis "gdal==$(gdal-config --version).*" --pip-args="--index-url https://gisidx.github.io/gwi"
```

```{note}
This is a third-party index, not an official PyPI channel: it is a convenience,
and you should weigh it against your own supply-chain policy. The
platform/Python-version coverage is the index's, so check its documentation if
your combination is unusual. The per-OS options below have no such caveat.
```

## Linux (Debian/Ubuntu)

First, install the GDAL system library and its `gdal-config` companion (see
[](../development/ubuntu.md) for PPA options if you need a specific version):

```sh
sudo apt install gdal-bin libgdal-dev
```

Then choose one of:

### Option A — reuse the system Python bindings (recommended)

If your distribution also ships `python3-gdal` (or you install it), you can
let the pipx venv see it instead of building a copy:

```sh
sudo apt install python3-gdal
pipx install dicogis --system-site-packages
```

### Option B — build GDAL into the isolated pipx venv

```sh
pipx install dicogis
pipx inject dicogis "gdal[numpy]==$(gdal-config --version).*"
```

This compiles the `gdal` Python package against your system `libgdal`, so it
needs `libgdal-dev` and a build toolchain (`build-essential`) available.

### Verify

```sh
dicogis-cli inventory --input-folder ./some/folder
```

## Windows

There is no official portable `gdal` wheel for Windows on PyPI. Two options:

### Option A — inject an unofficial prebuilt wheel

Download the wheel matching your Python version from
[cgohlke/geospatial-wheels](https://github.com/cgohlke/geospatial-wheels/releases)
(e.g. `GDAL-3.11.1-cp312-cp312-win_amd64.whl` for Python 3.12), then:

```powershell
pipx install dicogis
pipx inject dicogis C:\path\to\GDAL-3.11.1-cp312-cp312-win_amd64.whl
```

### Option B — use conda instead of pipx

If you'd rather avoid manual wheels, install DicoGIS in a
[conda](https://docs.conda.io/)/[mamba](https://mamba.readthedocs.io/)
environment, where GDAL is available as a prebuilt package:

```sh
conda create -n dicogis -c conda-forge python=3.12 gdal
conda activate dicogis
pip install dicogis
```

## The GUI extra

`dicogis-gui` additionally needs PyQt6, declared as an **optional** dependency
too (the `gui` extra), so `pipx install dicogis` / `dicogis-cli` never require
it:

```sh
pipx inject dicogis PyQt6
# or: pip install dicogis[gui]
```

## Prebuilt executables

If you'd rather not deal with GDAL at all, the
[releases on GitHub](https://github.com/Guts/DicoGIS/releases/latest) ship
standalone CLI/GUI executables (Windows and Ubuntu) that embed GDAL — no
Python or pipx required. See the "Try it" section on the [documentation
home page](../index.md).

## Docker

A container image for `dicogis-cli` is published to the [GitHub Container
Registry](https://github.com/Guts/DicoGIS/pkgs/container/dicogis), built on
top of the official [GDAL images](https://github.com/OSGeo/gdal/tree/master/docker)
so GDAL is already installed and version-matched — nothing to compile or
inject.

```sh
docker pull ghcr.io/guts/dicogis:latest
docker run --rm -v "$(pwd)":/data ghcr.io/guts/dicogis:latest \
    inventory --input-folder /data --output-path /data/dicogis_inventory.xlsx
```

The entrypoint is `dicogis-cli`, so any `dicogis-cli` subcommand/option works
the same way, e.g. `docker run --rm ghcr.io/guts/dicogis:latest --version`.
The working directory inside the container is `/data`; mount your input
folder (and/or `pg_service.conf` for PostGIS) there. Tags follow the project's
releases (`X.Y.Z`, `X.Y`) plus `edge` (latest `master`).
