#! python3  # noqa: E265


"""
Tests for the path helpers.

Usage from the repo root folder:
    pytest tests/test_utils_paths.py
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# standard library
import sys
from pathlib import Path

# 3rd party
import pytest

# project
from dicogis.utils.paths import absolute_path


# ##############################################################################
# ########## Tests ##################
# ##################################


def test_relative_path_is_made_absolute(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)

    assert absolute_path("data/parcels.shp") == tmp_path / "data" / "parcels.shp"


def test_dot_dot_components_are_collapsed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Unlike Path.absolute(), which keeps them."""
    monkeypatch.chdir(tmp_path)

    assert absolute_path("data/../vectors/./parcels.shp") == (
        tmp_path / "vectors" / "parcels.shp"
    )


def test_symlinks_are_not_followed(tmp_path: Path) -> None:
    """Unlike Path.resolve(), which follows them."""
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("creating symlinks isn't allowed here (Windows without rights)")

    assert absolute_path(link) == link
    assert absolute_path(link) != link.resolve()


def test_accepts_str_and_path(tmp_path: Path) -> None:
    assert absolute_path(str(tmp_path)) == absolute_path(tmp_path) == tmp_path


# ##############################################################################
# ##### Stand alone program ########
# ##################################
if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
