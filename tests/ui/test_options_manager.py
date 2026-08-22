#! python3

"""
Tests for OptionsManager save/load round-trip against the PyQt6 main window.

Usage from the repo root folder:
    pytest tests/ui/test_options_manager.py
"""

# #############################################################################
# ########## Libraries #############
# ##################################

# Standard library
from pathlib import Path

# package
from dicogis.ui.main_windows import DicoGIS
from dicogis.utils.options import OptionsManager

# #############################################################################
# ########## Tests ##################
# ##################################


def test_options_manager_save_and_load_round_trip(qtbot, tmp_path):
    ini_path = tmp_path / "options.ini"

    window = DicoGIS()
    qtbot.addWidget(window)
    window.settings = OptionsManager(str(ini_path))

    window.ddl_lang.setCurrentText("FR")
    window.tab_files.set_target_path(str(tmp_path))
    window.tab_files.set_filters_state({"opt_shp": "1", "opt_tab": "0"})
    window.tab_options.set_proxy_settings(
        {
            "proxy_needed": True,
            "proxy_type": False,
            "proxy_server": "proxy.example.com",
            "proxy_port": 8080,
            "proxy_user": "someone",
        }
    )

    assert window.settings.save_settings(window) is True
    assert ini_path.is_file()

    # build a fresh window and load the saved settings into it
    other_window = DicoGIS()
    qtbot.addWidget(other_window)
    other_window.settings = OptionsManager(str(ini_path))
    other_window.settings.load_settings(other_window)

    assert other_window.get_selected_language() == "FR"
    assert other_window.tab_files.get_filters_state()["opt_shp"] is True
    assert other_window.tab_files.get_filters_state()["opt_tab"] is False
    proxy_settings = other_window.tab_options.get_proxy_settings()
    assert proxy_settings["proxy_needed"] is True
    assert proxy_settings["proxy_server"] == "proxy.example.com"
    assert proxy_settings["proxy_port"] == 8080


def test_options_manager_first_use(tmp_path):
    ini_path = tmp_path / "does_not_exist.ini"
    settings = OptionsManager(str(ini_path))
    assert settings.first_use == 1
    assert Path(settings.confile) == ini_path
