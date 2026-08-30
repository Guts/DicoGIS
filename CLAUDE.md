# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

DicoGIS scans a folder tree (and/or PostGIS databases via `pg_service.conf`) for
geospatial datasets, extracts their metadata (CRS, geometry type, fields, extent,
size, etc.) using GDAL/OGR, and exports the result as an Excel workbook (`.xlsx`)
or JSON (optionally in "udata" flavor for publishing to a uData catalog). It ships
both a PyQt6 desktop GUI (`dicogis-gui`) and a Typer-based CLI (`dicogis-cli`),
distributed as PyInstaller executables for Windows/Linux.

## Common commands

### Environment setup

GDAL system libraries must be installed before the Python `gdal` package (version
must match `gdal-config --version`). See `docs/development/ubuntu.md` /
`windows.md` for OS-specific system requirements (incl. `python3-tk`).

```sh
python -m pip install -U pip setuptools wheel
python -m pip install -U gdal=="$(gdal-config --version).*"
python -m pip install -U -e .[gdal,dev,gui,test]
pre-commit install
```

### Running the app

```sh
dicogis-cli --help
dicogis-cli inventory --input-folder ./tests/fixtures --language EN
dicogis-gui
```

### Tests

Tests need fixture data and a PostGIS instance (see `docs/development/tests.md`):

```sh
git clone --depth=1 https://github.com/qgis/QGIS-Training-Data.git ./tests/fixtures/qgisdata
python -m pip install -U gisdata -t ./tests/fixtures
docker compose -f "tests/container/docker-compose.dev.yml" up -d --build
```

Run the full suite (config lives in `[tool.pytest.ini_options]` in `pyproject.toml`;
coverage is enabled by default via `addopts`):

```sh
pytest
```

Run a single test file or test:

```sh
pytest tests/test_utils_formatters.py
pytest tests/test_georeader_postgis.py::test_name -v
```

`tests/dev/` and `tests/_wip/` are excluded from collection (dev scratch scripts,
not part of the suite). PostGIS-related tests expect
`PGSERVICEFILE=./tests/fixtures/database/pg_service.conf`.

### Lint / format

Formatting/linting is enforced through pre-commit (ruff, ruff-format, black, isort,
pyupgrade, flake8 syntax-only check). Run everything pre-commit would run:

```sh
pre-commit run --all-files
```

CI's dedicated lint job only checks for syntax errors/undefined names:

```sh
flake8 dicogis --select=E9,F63,F7,F82
```

Line length: 88 (black/ruff-format/isort), docstrings are Google-style.

## Architecture

### Two entry points, one pipeline

`dicogis-cli` (`dicogis/cli/main.py`, a Typer app with `inventory` and `publish`
subcommands) and `dicogis-gui` (`dicogis/ui/main.py`, PyQt6) are thin wrappers
around the same core pipeline in `dicogis/georeaders`, `dicogis/listing`, and
`dicogis/export`. When changing core processing logic, check both entry points
for how they call into it — the GUI additionally wires up progress bars/counters
and runs long-running work in `QThread` workers (`dicogis/ui/workers.py`) that
the CLI passes as `None`.

GDAL is an optional extra (`pip install dicogis[gdal]`), so `dicogis-cli`/
`dicogis-gui` must stay importable without it (e.g. installed via `pipx` on a
system without GDAL): `dicogis/cli/cmd_inventory.py` and `dicogis/ui/main.py`
guard the GDAL-dependent imports (`ProcessingFiles`, `ReadPostGIS`, `DicoGIS`)
behind `GDAL_IS_AVAILABLE` (`dicogis/utils/environment.py`) and defer them into
the function/entry point body rather than importing eagerly at module scope —
keep new GDAL-dependent imports deferred the same way. See
`docs/usage/installation.md` for the pipx/GDAL install story.

PyQt6 is likewise an optional dependency (the `gui` extra) — `dicogis-cli`
does not import anything from `dicogis/ui`, so it works fully without it.
`dicogis-gui` (`dicogis/ui/main.py::dicogis_gui()`) imports `PyQt6.QtWidgets`
lazily and exits with a clear message if it's missing; `dicogis/ui/__init__.py`
is kept empty so importing `dicogis.ui`/`dicogis.ui.main` doesn't pull in PyQt6
before that guard runs (see `tests/test_ui_optional_pyqt6.py`).

### GUI widgets: `.ui` files + naming convention

GUI widgets are defined as Qt Designer `.ui` files, loaded dynamically at
runtime with `PyQt6.uic.loadUi()` — not built up imperatively in Python. Each
widget/dialog module has a matching `.ui` file of the same stem
(`dicogis/ui/wdg_tab_files.py` + `dicogis/ui/wdg_tab_files.ui`), loaded via
`Utilities().resolve_internal_path()` (so it resolves both from source and
from a frozen PyInstaller build) rather than `Path(__file__).parent`. Widgets
named in the `.ui` file (`objectName`) become attributes on `self` after
`loadUi()` — dynamic content (translated strings, values only known at
runtime, nested custom widgets) is still applied/composed in Python after the
load call.

File naming follows a prefix convention:
- `dlg_` — `QDialog` subclasses (`dicogis/ui/dialogs/dlg_database_connection.py`)
- `wdg_` — `QWidget` subclasses, including notebook tab pages
  (`wdg_tab_files.py`, `wdg_collapsible_frame.py`, `wdg_scrollable_table.py`, …)
- `mw_` — the `QMainWindow` (`dicogis/ui/mw_dicogis.py`)

Plain, unprefixed modules (`workers.py`, `main.py`) hold non-widget code
(QThread workers, the app entry point) and have no `.ui` counterpart.

### Processing pipeline

1. **Listing** (`dicogis/listing/geodata_listing.py`) — `find_geodata_files()`
   walks a folder tree and buckets file paths by format (shapefiles, MapInfo TAB,
   KML, GML, GeoJSON, GXT, rasters/GeoTIFF, CAD/DXF, file geodatabases: Esri
   FileGDB / SpatiaLite / GeoPackage). `check_usable_pg_services()` cross-checks
   requested PostgreSQL service names against `pg_service.conf` via
   `pgserviceparser`.
2. **Reading** (`dicogis/georeaders/`) — `GeoReaderBase` (`base_georeader.py`)
   holds shared GDAL/OGR setup (error handling via `GdalErrorHandler`, CRS/SRS
   introspection, extent, field listing, dependency-file discovery, dataset size).
   Format-specific readers (`read_vector_flat_dataset.py`,
   `read_vector_flat_geodatabase.py`, `read_raster.py`, `read_dxf.py`,
   `read_postgis.py`) subclass it and populate a `MetaDataset`
   (`dicogis/models/metadataset.py`) dataclass — the canonical in-memory
   representation of one dataset's metadata.
3. **Orchestration** (`dicogis/georeaders/process_files.py`) —
   `ProcessingFiles` maps each supported format to its reader class via
   `MATRIX_FORMAT_GEOREADER`, iterates the file lists produced by the listing
   step, wraps each in a `DatasetToProcess`, invokes the matching reader, and
   feeds the resulting `MetaDataset` into a serializer. `opt_analyze_*` flags
   (derived from the `--formats`/GUI checkboxes) gate which formats actually get
   processed; `opt_quick_fail` controls whether errors abort the run or get
   recorded per-dataset and skipped.
4. **Serialization** (`dicogis/export/`) — `MetadatasetSerializerBase`
   (`base_serializer.py`) defines `pre_serializing()` / `serialize_metadaset()` /
   `post_serializing()` and a factory,
   `get_serializer_from_parameters()`, that picks `MetadatasetSerializerXlsx`
   (`to_xlsx.py`) or `MetadatasetSerializerJson` (`to_json.py`, with a `flavor`
   of `"dicogis"` or `"udata"`) based on `OutputFormats`. Add a new output format
   here plus in `dicogis/constants.py::OutputFormats`.

Adding a new file format means: add it to `dicogis/constants.py`
(`FormatsVector`/`FormatsRaster`/`SUPPORTED_FORMATS`), extend
`find_geodata_files()` to detect it, register it (and its `opt_analyze_*` flag)
in `ProcessingFiles.MATRIX_FORMAT_GEOREADER`, and reuse or extend an existing
`GeoReaderBase` subclass.

### PostGIS path

Independent of the file pipeline: `ReadPostGIS` (`read_postgis.py`) connects using
a named `pg_service` (via GDAL's `PG:service=...` + `GDAL_POSTGIS_OPEN_OPTIONS`
from `constants.py`), iterates OGR layers, and serializes each with the same
serializer interface used by files. `dicogis/models/database_connection.py` holds
connection state/errors.

### i18n

Two separate mechanisms cover two separate concerns, split by whether GUI (PyQt6)
is involved:

- **CLI + shared processing pipeline** (`dicogis/export`, `dicogis/georeaders`,
  and anything reachable from `dicogis-cli`): `dicogis/utils/texts.py::TextsManager`
  loads strings from `dicogis/locale/lang_{EN,ES,FR}.xml` keyed by
  `AvailableLocales` (`dicogis/constants.py`) into a `localized_strings` dict,
  passed down explicitly through the processing pipeline (e.g. to
  `ProcessingFiles`, `MetadatasetSerializerBase`). This has no PyQt6 dependency,
  matching the CLI's own requirement to run without the `gui` extra installed.
  New pipeline-output strings (Excel/JSON field labels, error messages) should go
  through this mechanism rather than being hardcoded.
- **GUI widget text** (`dicogis/ui/*`, including dialogs): plain Qt native
  i18n — `self.tr("English source text")` calls, extracted into
  `dicogis/ui/i18n/dicogis_{en,fr,es}.ts` with `pylupdate6`, translated in Qt
  Linguist (or by hand), compiled to `.qm` with `lrelease`, and loaded via a
  `QTranslator` installed on the `QApplication` (`DicoGIS._install_qt_translator()`
  in `mw_dicogis.py`, called from `retranslate_ui()` before any `self.tr()` call,
  including the one done at startup and on every language-dropdown change). New
  widget-visible text should use `self.tr(...)` — never `TextsManager` — and the
  `.ts` files regenerated with:

  ```sh
  pylupdate6 dicogis/ui/*.py dicogis/ui/dialogs/*.py --ts dicogis/ui/i18n/dicogis_en.ts
  # repeat for _fr.ts / _es.ts, fill in <translation> entries, then compile:
  lrelease dicogis/ui/i18n/dicogis_fr.ts -qm dicogis/ui/i18n/dicogis_fr.qm
  lrelease dicogis/ui/i18n/dicogis_es.ts -qm dicogis/ui/i18n/dicogis_es.qm
  ```

  `dicogis_en.ts` is kept as the source-of-truth reference (never compiled/loaded
  at runtime: English is the source language, so untranslated `self.tr()` calls
  already return it with no `.qm` installed). Only `.qm` files ship with the
  package/frozen executables (`pyproject.toml` package-data, PyInstaller GUI
  builder scripts' `--add-data`), not the `.ts` sources.

### Cross-cutting utilities (`dicogis/utils/`)

- `journalizer.py::LogManager` — sets up console + rotating file logging under the
  platform app dir (`typer.get_app_dir`).
- `options.py` / `db_conf_reader.py` — read/write the `options.ini` config
  (template: `options_TPL.ini`) and `pg_service.conf` entries.
- `formatters.py`, `slugger.py`, `check_path.py`, `str2bound.py`,
  `checknorris.py` — small pure helpers (size formatting, slugifying, path
  validation) used across readers/exporters; covered directly by unit tests
  named `test_utils_*.py`.
- `notifier.py` — cross-platform desktop notification (`notify-py`) at the end of
  a run.

### Packaging

`builder/` contains the PyInstaller specs/scripts for Windows and Ubuntu, for
both the CLI and GUI executables, plus a Windows version-info templater. CI's
`builder_releaser.yml` workflow builds and publishes these. Version is
single-sourced from `dicogis/__about__.py::__version__` (`pyproject.toml` reads
it via `[tool.setuptools.dynamic]`).

A root-level `Dockerfile` (multi-stage, based on the official
`ghcr.io/osgeo/gdal:ubuntu-small-*` image so GDAL's Python bindings are
already present and version-matched — no `gdal` extra to compile) packages
`dicogis-cli` only, entrypoint `dicogis-cli`. Runtime dependencies are
installed with exact `==` pins (the versions `pyproject.toml`'s ranges
currently resolve to) before `pip install --no-deps .`, so the image is
reproducible instead of re-resolving ranges on every build — regenerate the
pins by rebuilding the image and copying the versions pip resolves. CI's
`docker_builder.yml` workflow builds it, smoke-tests `--version`/`--help`,
and pushes to `ghcr.io/guts/dicogis` (tags: `X.Y.Z`/`X.Y` on releases, `edge`
on `master`) via `docker/build-push-action` (pinned to a commit SHA, like the
other third-party actions it uses).

## Contributing

Full guidelines: `CONTRIBUTING.md`. What matters most for changes made here:

- **Commit messages** follow [Conventional Commits](https://www.conventionalcommits.org/):
  `<type>(<scope>): <description>` (scope optional), e.g.
  `fix(cli,gui): defer GDAL imports so dicogis-cli/gui work without it`. Common
  types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`, `build`.
- **Branch names** are prefixed to drive auto-labeling and release-notes
  categorization (`.github/labeler.yml` / `.github/release.yml`): `fix/…` or
  `hotfix/…` (bug fix), `feature/…` or `improve/…` (enhancement), `docs/…`,
  `packaging/…`, `tooling/…`, `cli/…`.
- **Pull requests** should fill out `.github/PULL_REQUEST_TEMPLATE.md`
  (auto-filled on GitHub) — including the "Type of change" checklist and
  confirming `pre-commit run --all-files` / `pytest` were run where relevant.
- **AI/LLM disclosure is required**: any PR/commit produced with AI assistance
  must disclose the transparency level (per
  [VisiData's scale](https://www.visidata.org/blog/2026/ai/), summarized as a
  table in `CONTRIBUTING.md`'s "AI/LLM-assisted contributions" section), the
  model used, and a link to the session — in the PR description's "AI/LLM
  disclosure" section and/or as commit trailers (`AI-Level:`, `AI-Model:`,
  `Co-Authored-By:`, `Claude-Session:` — see recent commit history for the
  exact trailer format). A human must still have reviewed and tested the
  change themselves, whatever the level.

## Conventions

- Files start with the shebang comment `#! python3  # noqa: E265` and use the
  `# ###...` section-banner comment style (Libraries / Globals / Classes /
  Functions) seen throughout `dicogis/`; new files should follow the same layout
  for consistency.
- Google-style docstrings.
- GDAL/OGR objects require `gdal.UseExceptions()` / `ogr.UseExceptions()` (set up
  in `GeoReaderBase.__init__`) — don't re-open datasets without going through a
  `GeoReaderBase` subclass, since error handling and open-flag/option logic lives
  there.
- Prefer the standard library over new third-party dependencies where practical
  (see `CONTRIBUTING.md` "Security" section) given the project targets
  large-scale IT infrastructures.
- GUI widgets: `.ui` files loaded with `uic.loadUi()`, not built up in Python —
  see "GUI widgets: `.ui` files + naming convention" above.
