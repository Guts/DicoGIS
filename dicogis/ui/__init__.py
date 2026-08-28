#! python3  # noqa: E265

# PyQt6 is an optional dependency (see pyproject.toml `gui` extra): submodules of
# this package import it at module level, so this __init__.py must not re-export
# them eagerly, or importing dicogis.ui.main (the dicogis-gui entry point) would
# break entirely when PyQt6 isn't installed, before the deferred/guarded imports
# in dicogis_gui() ever get a chance to run.
