#! python3  # noqa: E265


"""
Tests for the per-user application folder helper.

Usage from the repo root folder:
    pytest tests/test_utils_app_dir.py
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# standard library
import sys
from pathlib import Path

# 3rd party
import pytest
import typer

# project
from dicogis.utils.app_dir import get_app_dir


# ##############################################################################
# ########## Functions #############
# ##################################


def _set_home(monkeypatch: pytest.MonkeyPatch, home: str) -> None:
    """Fix the home folder whatever the OS: on Windows, Path.home() reads
    USERPROFILE and ignores HOME, so setting HOME alone isn't enough."""
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: cls(home)))


# ##############################################################################
# ########## Tests ##################
# ##################################


@pytest.mark.parametrize("app_name", ["DicoGIS", "Foo Bar"])
def test_same_folder_as_typer_on_this_platform(app_name: str) -> None:
    """Earlier versions used typer.get_app_dir(force_posix=True): existing
    settings and logs must be found at the same place."""
    assert get_app_dir(app_name) == Path(
        typer.get_app_dir(app_name=app_name, force_posix=True)
    )


def test_default_app_name_is_dicogis(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    _set_home(monkeypatch, "/home/someone")

    assert get_app_dir() == Path("/home/someone/.dicogis")


def test_posix_name_is_lowercase_and_hyphenated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "platform", "darwin")
    _set_home(monkeypatch, "/Users/someone")

    assert get_app_dir("Foo  Bar") == Path("/Users/someone/.foo-bar")


def test_windows_uses_appdata(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", "/roaming")

    assert get_app_dir("DicoGIS") == Path("/roaming", "DicoGIS")


def test_windows_falls_back_to_home_without_appdata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.delenv("APPDATA", raising=False)
    _set_home(monkeypatch, "/home/someone")

    assert get_app_dir("DicoGIS") == Path("/home/someone", "DicoGIS")


# ##############################################################################
# ##### Stand alone program ########
# ##################################
if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
