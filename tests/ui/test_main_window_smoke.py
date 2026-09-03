#! python3

"""
Smoke tests for the PyQt6 main window.

Usage from the repo root folder:
    pytest tests/ui/test_main_window_smoke.py
"""

# #############################################################################
# ########## Libraries #############
# ##################################

# standard library
from unittest.mock import MagicMock

# package
from dicogis.ui.mw_dicogis import DicoGIS
from dicogis.ui.workers import QtProgressReporter


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


def test_main_window_check_fields_accepts_any_single_format(
    qtbot, monkeypatch, tmp_path
):
    """Ticking one single format filter, whichever it is, is enough to run.

    Regression: check_fields() enumerated the filters by hand and had left
    "opt_gxt" out, so a Geoconcept-only selection was rejected with "Any
    format selected". Looping over every filter keeps this honest when a
    format is added.
    """
    window = DicoGIS()
    qtbot.addWidget(window)

    shown_messages = []
    monkeypatch.setattr(
        "dicogis.ui.mw_dicogis.QMessageBox.critical",
        staticmethod(lambda *args, **kwargs: shown_messages.append(args)),
    )
    window.tab_files.set_target_path(str(tmp_path))

    all_filters_off = {key: "0" for key in window.tab_files.get_filters_state()}
    assert len(all_filters_off) > 1, "no format filter found to check"

    for filter_name in all_filters_off:
        window.tab_files.set_filters_state(all_filters_off)
        window.tab_files.set_filters_state({filter_name: "1"})

        assert window.check_fields(tab_data_type=0) is True, (
            f"a selection limited to {filter_name} was rejected"
        )
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


def test_main_window_close_requests_cancellation(qtbot):
    """Closing the window must ask the running operation to stop.

    Regression: closeEvent() only called QThread.quit(), which asks a thread's
    event loop to return -- something a worker blocked inside its own run()
    never reaches. Closing during a scan froze the window for the whole
    wait() timeout and still left the thread running.
    """
    window = DicoGIS()
    qtbot.addWidget(window)
    window._progress_reporter = QtProgressReporter(window)
    assert window._progress_reporter.is_canceled() is False

    window.close()

    assert window._progress_reporter.is_canceled() is True


def test_main_window_close_without_a_running_operation(qtbot):
    """No operation ever started: closing must not raise on the absent
    progress reporter."""
    window = DicoGIS()
    qtbot.addWidget(window)
    assert window._progress_reporter is None

    window.close()


def test_main_window_hides_cancel_button_when_a_run_ends(qtbot, monkeypatch):
    """Every path out of a run hides the cancel button.

    Regression: each handler hid it on its own and the PostGIS one had been
    forgotten, so the button stayed visible after a successful database run.
    """
    window = DicoGIS()
    qtbot.addWidget(window)
    monkeypatch.setattr("dicogis.ui.mw_dicogis.launch", lambda url: None)
    monkeypatch.setattr(
        "dicogis.ui.mw_dicogis.send_system_notify", lambda **kwargs: None
    )
    window.serializer = MagicMock()

    for end_of_run in (
        lambda: window._on_db_processing_finished(total_layers=3),
        lambda: window._on_files_processing_finished(total_files=3),
        lambda: window._on_processing_canceled(),
    ):
        window._enable_cancel_button(True)
        # isHidden() rather than isVisible(): the window itself is never shown
        # in tests, so every child reports isVisible() False regardless
        assert window.btn_cancel.isHidden() is False
        assert window.btn_cancel.isEnabled() is True

        end_of_run()

        assert window.btn_cancel.isEnabled() is False
        assert window.btn_cancel.isHidden() is True


def test_main_window_folder_selected_sets_default_output_name(qtbot):
    window = DicoGIS()
    qtbot.addWidget(window)

    window.on_folder_selected("/tmp/some_folder")

    assert window.ent_outxl_filename.text().startswith("DicoGIS_some_folder_")
    assert window._scan_thread is not None

    with qtbot.waitSignal(window._scan_thread.finished, timeout=5000):
        pass
