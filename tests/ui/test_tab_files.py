#! python3

"""
Tests for the TabFiles widget (folder/format filters tab).

Usage from the repo root folder:
    pytest tests/ui/test_tab_files.py
"""

# #############################################################################
# ########## Libraries #############
# ##################################

# standard library
from unittest.mock import patch

# package
from dicogis.ui.wdg_tab_files import CHECKBOX_TO_FORMAT, RASTER_FORMATS, TabFiles


# #############################################################################
# ########## Tests ##################
# ##################################


def test_formats_supported_by_the_installed_gdal_stay_enabled(qtbot):
    """With every format reported as supported, no checkbox is touched."""
    with patch(
        "dicogis.ui.wdg_tab_files.is_format_supported_by_gdal", return_value=True
    ):
        widget = TabFiles()
    qtbot.addWidget(widget)

    for checkbox_name in (*CHECKBOX_TO_FORMAT, "cbx_rast"):
        checkbox = getattr(widget, checkbox_name)
        assert checkbox.isEnabled(), checkbox_name
        assert checkbox.toolTip() == "", checkbox_name


def test_format_unsupported_by_gdal_disables_its_checkbox(qtbot):
    """A format whose driver is missing gets its checkbox unchecked, disabled
    and given an explanatory tooltip (e.g. Geoconcept/.gxt on a GDAL build
    without the optional Geoconcept driver)."""

    def fake_is_supported(format_name, available_drivers=None):
        return format_name != "gxt"

    with patch(
        "dicogis.ui.wdg_tab_files.is_format_supported_by_gdal",
        side_effect=fake_is_supported,
    ):
        widget = TabFiles()
    qtbot.addWidget(widget)

    assert widget.cbx_gxt.isEnabled() is False
    assert widget.cbx_gxt.isChecked() is False
    assert widget.cbx_gxt.toolTip() != ""

    # unrelated checkboxes are left untouched
    assert widget.cbx_shp.isEnabled() is True
    assert widget.cbx_shp.toolTip() == ""


def test_raster_checkbox_disabled_when_no_raster_driver_available(qtbot):
    """cbx_rast covers ecw/geotiff/jpeg at once: it is only disabled when
    none of them is supported."""
    with patch(
        "dicogis.ui.wdg_tab_files.is_format_supported_by_gdal", return_value=False
    ):
        widget = TabFiles()
    qtbot.addWidget(widget)

    assert widget.cbx_rast.isEnabled() is False
    assert widget.cbx_rast.isChecked() is False


def test_raster_checkbox_enabled_when_at_least_one_raster_driver_available(qtbot):
    def fake_is_supported(format_name, available_drivers=None):
        return format_name == "geotiff"

    with patch(
        "dicogis.ui.wdg_tab_files.is_format_supported_by_gdal",
        side_effect=fake_is_supported,
    ):
        widget = TabFiles()
    qtbot.addWidget(widget)

    assert widget.cbx_rast.isEnabled() is True


def test_checkbox_to_format_mapping_matches_raster_formats_constant():
    """Sanity check: RASTER_FORMATS lists exactly the FormatsRaster member
    names, kept separate from CHECKBOX_TO_FORMAT since cbx_rast has no
    single format of its own."""
    assert set(RASTER_FORMATS) == {"ecw", "geotiff", "jpeg"}
    assert "cbx_rast" not in CHECKBOX_TO_FORMAT


# #############################################################################
# ##### Main #######################
# ##################################
if __name__ == "__main__":
    import sys

    sys.exit(__import__("pytest").main([__file__]))
