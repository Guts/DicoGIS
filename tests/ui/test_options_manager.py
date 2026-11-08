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

    window.cbb_lang.setCurrentText("FR")
    window.set_selected_output_format("udata")
    window.wdg_tab_files.set_target_path(str(tmp_path))
    window.wdg_tab_files.set_filters_state({"opt_shp": "1", "opt_tab": "0"})
    window.wdg_tab_settings.set_proxy_settings(
        {
            "proxy_needed": True,
            "proxy_type": False,
            "proxy_server": "proxy.example.com",
            "proxy_port": 8080,
            "proxy_user": "someone",
        }
    )
    window.wdg_tab_publish.set_input_folder(str(tmp_path))
    window.wdg_tab_publish.lne_udata_api_url_base.setText(
        "https://udata-test.example/api/"
    )
    window.wdg_tab_publish.lne_udata_api_version.setText("2")
    window.wdg_tab_publish.lne_udata_organization_id.setText("some-org-id")
    window.wdg_tab_publish.lne_udata_api_key.setText("super-secret-key")

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
    assert other_window.get_selected_output_format() == "udata"
    assert other_window.wdg_tab_files.get_filters_state()["opt_shp"] is True
    assert other_window.wdg_tab_files.get_filters_state()["opt_tab"] is False
    proxy_settings = other_window.wdg_tab_settings.get_proxy_settings()
    assert proxy_settings["proxy_needed"] is True
    assert proxy_settings["proxy_server"] == "proxy.example.com"
    assert proxy_settings["proxy_port"] == 8080
    assert other_window.wdg_tab_publish.get_input_folder() == str(tmp_path)
    assert (
        other_window.wdg_tab_publish.get_udata_api_url_base()
        == "https://udata-test.example/api/"
    )
    assert other_window.wdg_tab_publish.get_udata_api_version() == "2"
    assert other_window.wdg_tab_publish.get_udata_organization_id() == "some-org-id"
    # the API key is never persisted, so it stays empty after a load
    assert other_window.wdg_tab_publish.get_udata_api_key() == ""


def test_options_manager_geonetwork_round_trip(qtbot, tmp_path):
    ini_path = tmp_path / "options.ini"

    window = DicoGIS()
    qtbot.addWidget(window)
    window.settings = OptionsManager(str(ini_path))
    tab = window.wdg_tab_publish
    tab.set_publish_target("geonetwork")
    tab.lne_geonetwork_url_base.setText("https://catalogue.example/geonetwork?a=%20")
    tab.lne_geonetwork_portal.setText("inspire")
    tab.lne_geonetwork_username.setText("editor")
    tab.lne_geonetwork_password.setText("super-secret-password")
    tab.lne_geonetwork_authcfg.setText("abc1234")
    tab.lne_geonetwork_group.setText("2")
    tab.lne_geonetwork_categories.setText("1, 3")
    tab._set_geonetwork_update_mode("complete")
    tab.cbx_geonetwork_publish_to_all.setChecked(True)
    tab.cbx_geonetwork_reject_if_invalid.setChecked(True)

    assert window.settings.save_settings(window) is True
    saved_options = ini_path.read_text(encoding="UTF-8")
    assert "super-secret-password" not in saved_options
    assert "abc1234" in saved_options

    other_window = DicoGIS()
    qtbot.addWidget(other_window)
    other_window.settings = OptionsManager(str(ini_path))
    other_window.settings.load_settings(other_window)

    other_tab = other_window.wdg_tab_publish
    assert other_tab.get_publish_target() == "geonetwork"
    assert other_tab.stk_publish_target.currentWidget() is other_tab.wdg_page_geonetwork
    assert other_tab.get_geonetwork_url_base() == (
        "https://catalogue.example/geonetwork?a=%20"
    )
    assert other_tab.get_geonetwork_portal() == "inspire"
    assert other_tab.get_geonetwork_username() == "editor"
    assert other_tab.get_geonetwork_password() == ""
    assert other_tab.lne_geonetwork_authcfg.text() == "abc1234"
    assert other_tab.get_geonetwork_group() == "2"
    assert other_tab.get_geonetwork_categories() == ["1", "3"]
    assert other_tab.get_geonetwork_update_mode() == "complete"
    assert other_tab.cbx_geonetwork_publish_to_all.isChecked() is True
    assert other_tab.cbx_geonetwork_reject_if_invalid.isChecked() is True


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
    window.set_selected_output_format("json")

    window.settings.load_settings(window)

    assert window.wdg_tab_publish.get_input_folder() == ""
    # no publication target saved yet: uData stays the default one
    assert window.wdg_tab_publish.get_publish_target() == "udata"
    # no output_format saved yet: the initial (environment/default) one is kept
    assert window.get_selected_output_format() == "json"


def test_options_manager_first_use(tmp_path):
    ini_path = tmp_path / "does_not_exist.ini"
    settings = OptionsManager(str(ini_path))
    assert settings.first_use == 1
    assert Path(settings.confile) == ini_path
