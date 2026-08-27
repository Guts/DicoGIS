#! python3

"""
Smoke tests for the PyQt6 main window.

Usage from the repo root folder:
    pytest tests/ui/test_main_window_smoke.py
"""

# #############################################################################
# ########## Libraries #############
# ##################################

# package
from dicogis.ui.mw_dicogis import DicoGIS

# #############################################################################
# ########## Tests ##################
# ##################################


def test_main_window_constructs(qtbot):
    window = DicoGIS()
    qtbot.addWidget(window)

    assert window.nb.count() == 5


def test_main_window_retranslate_ui_all_languages(qtbot):
    window = DicoGIS()
    qtbot.addWidget(window)

    for language_code in ("EN", "FR", "ES", "EN"):
        window.ddl_lang.setCurrentText(language_code)
        window.retranslate_ui()

        assert window.welcome.text()
        assert window.get_selected_language() == language_code


def test_main_window_check_fields_requires_folder(qtbot, monkeypatch):
    window = DicoGIS()
    qtbot.addWidget(window)

    shown_messages = []
    monkeypatch.setattr(
        "dicogis.ui.mw_dicogis.QMessageBox.critical",
        staticmethod(lambda *args, **kwargs: shown_messages.append(args)),
    )

    window.tab_files.set_target_path("")
    assert window.check_fields(tab_data_type=0) is False
    assert shown_messages


def test_main_window_check_fields_requires_format(qtbot, monkeypatch):
    window = DicoGIS()
    qtbot.addWidget(window)

    monkeypatch.setattr(
        "dicogis.ui.mw_dicogis.QMessageBox.critical",
        staticmethod(lambda *args, **kwargs: None),
    )

    window.tab_files.set_target_path("/tmp")
    window.tab_files.set_filters_state(
        {key: "0" for key in window.tab_files.get_filters_state()}
    )
    assert window.check_fields(tab_data_type=0) is False


def test_main_window_check_fields_accepts_geopackage_only(qtbot, monkeypatch, tmp_path):
    window = DicoGIS()
    qtbot.addWidget(window)

    shown_messages = []
    monkeypatch.setattr(
        "dicogis.ui.mw_dicogis.QMessageBox.critical",
        staticmethod(lambda *args, **kwargs: shown_messages.append(args)),
    )

    window.tab_files.set_target_path(str(tmp_path))
    window.tab_files.set_filters_state(
        {key: "0" for key in window.tab_files.get_filters_state()}
    )
    window.tab_files.set_filters_state({"opt_gpkg": "1"})

    assert window.check_fields(tab_data_type=0) is True
    assert not shown_messages


def test_main_window_check_fields_requires_publish_input_folder(qtbot, monkeypatch):
    window = DicoGIS()
    qtbot.addWidget(window)

    shown_messages = []
    monkeypatch.setattr(
        "dicogis.ui.mw_dicogis.QMessageBox.critical",
        staticmethod(lambda *args, **kwargs: shown_messages.append(args)),
    )

    window.tab_publish.set_input_folder("")
    assert window.check_fields(tab_data_type=3) is False
    assert shown_messages


def test_main_window_check_fields_requires_publish_api_key(
    qtbot, monkeypatch, tmp_path
):
    window = DicoGIS()
    qtbot.addWidget(window)

    monkeypatch.setattr(
        "dicogis.ui.mw_dicogis.QMessageBox.critical",
        staticmethod(lambda *args, **kwargs: None),
    )

    window.tab_publish.set_input_folder(str(tmp_path))
    window.tab_publish.ent_udata_api_key.setText("")
    assert window.check_fields(tab_data_type=3) is False


def test_main_window_folder_selected_sets_default_output_name(qtbot):
    window = DicoGIS()
    qtbot.addWidget(window)

    window.on_folder_selected("/tmp/some_folder")

    assert window.ent_outxl_filename.text().startswith("DicoGIS_some_folder_")
    assert window._scan_thread is not None

    with qtbot.waitSignal(window._scan_thread.finished, timeout=5000):
        pass
