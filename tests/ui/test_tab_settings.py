#! python3

"""
Tests for the TabSettings widget:

- parallel-scan options (checkbox + max workers spinbox): env var defaults,
  get/set round-trip, and the kwargs handed to
  FolderScanWorker/find_geodata_files();
- proxy settings group box: toggling and get/set round-trip.

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


def test_proxy_group_box_stays_toggleable(qtbot):
    """The proxy group box must remain clickable at all times.

    Regression: the .ui declared it `enabled=false` and the widget wired
    `toggled -> setEnabled`, so it started disabled and, once unchecked,
    disabled itself -- leaving no way to (re)enable proxy support from the
    GUI at all.
    """
    widget = TabSettings()
    qtbot.addWidget(widget)

    assert widget.FrOptProxy.isEnabled() is True

    for checked in (True, False, True):
        widget.FrOptProxy.setChecked(checked)
        assert widget.FrOptProxy.isChecked() is checked
        assert widget.FrOptProxy.isEnabled() is True


def test_proxy_fields_follow_the_check_state(qtbot):
    """A checkable QGroupBox already enables/disables its children with its
    check state: the proxy inputs must follow it, without any extra wiring.
    """
    widget = TabSettings()
    qtbot.addWidget(widget)
    proxy_inputs = (
        widget.prox_ent_host,
        widget.prox_ent_port,
        widget.prox_ent_user,
    )

    widget.FrOptProxy.setChecked(False)
    assert not any(proxy_input.isEnabled() for proxy_input in proxy_inputs)

    widget.FrOptProxy.setChecked(True)
    assert all(proxy_input.isEnabled() for proxy_input in proxy_inputs)


def test_get_set_proxy_settings_round_trip(qtbot):
    """Proxy settings round-trip through set_proxy_settings()/
    get_proxy_settings(), as OptionsManager persists them to options.ini."""
    widget = TabSettings()
    qtbot.addWidget(widget)

    widget.set_proxy_settings(
        {
            "proxy_needed": "1",
            "proxy_type": "0",
            "proxy_server": "proxy.example.org",
            "proxy_port": "8080",
            "proxy_user": "jdoe",
        }
    )

    assert widget.get_proxy_settings() == {
        "proxy_needed": True,
        "proxy_type": False,
        "proxy_server": "proxy.example.org",
        "proxy_port": 8080,
        "proxy_user": "jdoe",
    }


# #############################################################################
# ##### Main #######################
# ##################################
if __name__ == "__main__":
    import sys

    sys.exit(__import__("pytest").main([__file__]))
