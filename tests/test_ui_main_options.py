#! python3  # noqa: E265


"""
Tests for the settings `dicogis-gui` reads back before a QApplication exists
(interface style, verbose logging), which it must look for in the very file
OptionsManager saves to.

Imports only `dicogis.ui.main`, which stays free of PyQt6/GDAL (see
tests/test_ui_optional_pyqt6.py), so these run without either installed.

Usage from the repo root folder:
    pytest tests/test_ui_main_options.py
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# standard library
from configparser import ConfigParser
from pathlib import Path

# package
from dicogis.ui.main import _get_persisted_option
from dicogis.utils.options import OptionsManager


# ##############################################################################
# ########## Functions #############
# ##################################


def _write_options_file(ini_path: Path, style: str) -> None:
    """Write an options.ini holding a single interface style."""
    config = ConfigParser()
    config["ui"] = {"style": style}
    with ini_path.open(mode="w", encoding="UTF-8") as configfile:
        config.write(configfile)


# ##############################################################################
# ########## Tests ##################
# ##################################


def test_reads_the_file_options_manager_writes_to(tmp_path, monkeypatch):
    """Regression: the lookup used a relative "options.ini", resolved against
    the current working directory, while OptionsManager saves to a
    per-platform user config folder. Nothing was ever read back, so the
    interface style and the verbose-logging flag silently reverted to their
    defaults on every start.
    """
    ini_path = tmp_path / "options.ini"
    _write_options_file(ini_path, style="Fusion")
    monkeypatch.setattr("dicogis.ui.main.DEFAULT_OPTIONS_FILEPATH", ini_path)

    # the file just written is indeed the one OptionsManager would save to
    assert Path(OptionsManager(ini_path).confile) == ini_path.resolve()

    assert _get_persisted_option("ui", "style") == "Fusion"


def test_ignores_a_stray_options_ini_in_the_current_directory(tmp_path, monkeypatch):
    """Only the settings file counts, not a same-named file that happens to
    sit in the folder the GUI was started from."""
    ini_path = tmp_path / "options.ini"
    _write_options_file(ini_path, style="Fusion")
    monkeypatch.setattr("dicogis.ui.main.DEFAULT_OPTIONS_FILEPATH", ini_path)

    decoy_folder = tmp_path / "elsewhere"
    decoy_folder.mkdir()
    _write_options_file(decoy_folder / "options.ini", style="Windows")
    monkeypatch.chdir(decoy_folder)

    assert _get_persisted_option("ui", "style") == "Fusion"


def test_does_not_read_the_current_working_directory(tmp_path, monkeypatch):
    """Same regression as above, expressed without touching the module's
    constant, so it fails on the previous code for the right reason rather
    than because the constant did not exist yet: a stray options.ini in the
    folder the GUI happens to be started from is exactly what the old lookup
    read, and must now be ignored.

    Assumes the machine's own saved settings, if any, do not name this style.
    """
    _write_options_file(tmp_path / "options.ini", style="AStyleNobodyWouldPick")
    monkeypatch.chdir(tmp_path)

    assert _get_persisted_option("ui", "style") != "AStyleNobodyWouldPick"


def test_returns_none_when_no_settings_file_exists(tmp_path, monkeypatch):
    """First run: nothing saved yet, and the caller falls back to its default."""
    monkeypatch.setattr(
        "dicogis.ui.main.DEFAULT_OPTIONS_FILEPATH", tmp_path / "never_saved.ini"
    )

    assert _get_persisted_option("ui", "style") is None


def test_returns_none_for_an_option_absent_from_the_file(tmp_path, monkeypatch):
    """A file written by an older version, predating the option."""
    ini_path = tmp_path / "options.ini"
    _write_options_file(ini_path, style="Fusion")
    monkeypatch.setattr("dicogis.ui.main.DEFAULT_OPTIONS_FILEPATH", ini_path)

    assert _get_persisted_option("basics", "debug") is None


# ##############################################################################
# ##### Stand alone program ########
# ##################################
if __name__ == "__main__":
    import sys

    sys.exit(__import__("pytest").main([__file__]))
