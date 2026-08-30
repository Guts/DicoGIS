#! python3

"""
Tests for the TabSettings widget's parallel-scan options (checkbox + max
workers spinbox): env var defaults, get/set round-trip, and the kwargs
handed to FolderScanWorker/find_geodata_files().

Usage from the repo root folder:
    pytest tests/ui/test_tab_settings.py
"""

# #############################################################################
# ########## Libraries #############
# ##################################

# standard library
from unittest.mock import patch

# package
from dicogis.ui.wdg_tab_settings import TabSettings

# #############################################################################
# ########## Tests ##################
# ##################################


def test_parallel_scan_options_default_off_and_auto(qtbot):
    """Without env vars set, parallel scan is off and max workers is 0
    ("Auto"), translating to parallel_scan=False/max_workers=None."""
    with patch.dict("os.environ", {}, clear=False):
        for var in ("DICOGIS_LISTING_PARALLEL_SCAN", "DICOGIS_LISTING_MAX_WORKERS"):
            import os

            os.environ.pop(var, None)
        widget = TabSettings()
    qtbot.addWidget(widget)

    assert widget.opt_parallel_scan.isChecked() is False
    assert widget.opt_max_workers.value() == 0
    assert widget.get_listing_scan_kwargs() == {
        "parallel_scan": False,
        "max_workers": None,
    }


def test_parallel_scan_options_read_from_env_vars(qtbot):
    """DICOGIS_LISTING_PARALLEL_SCAN/DICOGIS_LISTING_MAX_WORKERS seed the
    checkbox/spinbox, matching the same env vars read by dicogis-cli's
    --opt-parallel-scan/--listing-max-workers options."""
    with patch.dict(
        "os.environ",
        {
            "DICOGIS_LISTING_PARALLEL_SCAN": "True",
            "DICOGIS_LISTING_MAX_WORKERS": "12",
        },
    ):
        widget = TabSettings()
    qtbot.addWidget(widget)

    assert widget.opt_parallel_scan.isChecked() is True
    assert widget.opt_max_workers.value() == 12
    assert widget.get_listing_scan_kwargs() == {
        "parallel_scan": True,
        "max_workers": 12,
    }


def test_get_set_export_options_round_trip_for_parallel_scan(qtbot):
    """listing_parallel_scan/listing_max_workers round-trip through
    get_export_options()/set_export_options(), like every other setting
    persisted by OptionsManager."""
    widget = TabSettings()
    qtbot.addWidget(widget)

    widget.set_export_options(
        {"listing_parallel_scan": "True", "listing_max_workers": "5"}
    )

    options = widget.get_export_options()
    assert options["listing_parallel_scan"] is True
    assert options["listing_max_workers"] == 5
    assert widget.get_listing_scan_kwargs() == {
        "parallel_scan": True,
        "max_workers": 5,
    }


# #############################################################################
# ##### Main #######################
# ##################################
if __name__ == "__main__":
    import sys

    sys.exit(__import__("pytest").main([__file__]))
