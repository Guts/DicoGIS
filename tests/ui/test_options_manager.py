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
from dicogis.ui.mw_dicogis import DicoGIS
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
    window.tab_publish.set_input_folder(str(tmp_path))
    window.tab_publish.ent_udata_api_url_base.setText("https://udata-test.example/api/")
    window.tab_publish.ent_udata_api_version.setText("2")
    window.tab_publish.ent_udata_organization_id.setText("some-org-id")
    window.tab_publish.ent_udata_api_key.setText("super-secret-key")

    assert window.settings.save_settings(window) is True
    assert ini_path.is_file()
    # the API key must never be persisted to options.ini
    assert "super-secret-key" not in ini_path.read_text(encoding="UTF-8")

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
    assert other_window.tab_publish.get_input_folder() == str(tmp_path)
    assert (
        other_window.tab_publish.get_udata_api_url_base()
        == "https://udata-test.example/api/"
    )
    assert other_window.tab_publish.get_udata_api_version() == "2"
    assert other_window.tab_publish.get_udata_organization_id() == "some-org-id"
    # the API key is never persisted, so it stays empty after a load
    assert other_window.tab_publish.get_udata_api_key() == ""


def test_options_manager_load_settings_without_udata_section(qtbot, tmp_path):
    """Older options.ini files predating the "udata" section must still load fine."""
    ini_path = tmp_path / "options.ini"
    ini_path.write_text(
        "[basics]\n"
        "def_codelang = EN\n"
        "def_rep = \n"
        "def_tab = 0\n"
        "export_prettify_size = 1\n"
        "export_raw_path = 0\n"
        "quick_fail = 0\n"
        "notification_sound = 1\n"
        "\n"
        "[filters]\n"
        "\n"
        "[database]\n"
        "last_used_pg_service = \n"
        "opt_views = 0\n"
        "\n"
        "[proxy]\n"
        "proxy_needed = 0\n"
        "proxy_type = 0\n"
        "proxy_server = proxy.server.com\n"
        "proxy_port = 80\n"
        "proxy_user = proxy_user\n",
        encoding="UTF-8",
    )

    window = DicoGIS()
    qtbot.addWidget(window)
    window.settings = OptionsManager(str(ini_path))

    window.settings.load_settings(window)

    assert window.tab_publish.get_input_folder() == ""


def test_options_manager_first_use(tmp_path):
    ini_path = tmp_path / "does_not_exist.ini"
    settings = OptionsManager(str(ini_path))
    assert settings.first_use == 1
    assert Path(settings.confile) == ini_path
