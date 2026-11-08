#! python3

"""
Tests for the dispatch of the publication by the main window: which catalog, which way
of running it, what's checked before.

Usage from the repo root folder:
    pytest tests/ui/test_main_window_publish.py
"""

# #############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import sys
import types
from functools import partial
from pathlib import Path

# 3rd party
import pytest

# package
from dicogis.export.catalog_record import CatalogRecordSettings
from dicogis.export.to_iso19139 import MetadatasetSerializerIso19139
from dicogis.publishing import geonetwork, udata
from dicogis.publishing.report import PublishReport
from dicogis.ui.mw_dicogis import DicoGIS
from dicogis.utils.http.backend_qgis import QgisHttpClient
from dicogis.utils.http.backend_requests import RequestsHttpClient


# #############################################################################
# ########## Fixtures ##############
# ##################################


@pytest.fixture
def window(qtbot, monkeypatch, tmp_path) -> DicoGIS:
    """Main window with no notification and no message box."""
    monkeypatch.setattr(
        "dicogis.ui.mw_dicogis.send_system_notify", lambda **kwargs: None
    )
    main_window = DicoGIS()
    qtbot.addWidget(main_window)
    main_window.wdg_tab_publish.set_input_folder(str(tmp_path))
    return main_window


@pytest.fixture
def errors(monkeypatch) -> list[str]:
    """Record what's shown in error message boxes."""
    messages: list[str] = []
    monkeypatch.setattr(
        "dicogis.ui.mw_dicogis.QMessageBox.critical",
        lambda _parent, _title, message: messages.append(message),
    )
    return messages


def _fill_geonetwork(window: DicoGIS) -> None:
    tab = window.wdg_tab_publish
    tab.set_publish_target("geonetwork")
    tab.lne_geonetwork_url_base.setText("https://gn.example/geonetwork")
    tab.lne_geonetwork_group.setText("2")
    tab.lne_geonetwork_username.setText("editor")
    tab.lne_geonetwork_password.setText("s3cret")


class _FakeSignal:
    def __init__(self) -> None:
        self.slots = []

    def connect(self, slot) -> None:
        self.slots.append(slot)


class _FakeTaskReporter:
    def __init__(self) -> None:
        self.cancel_requested = False

    def request_cancel(self) -> None:
        self.cancel_requested = True


class _FakeTask:
    def __init__(self, description, publish_function, on_finished, on_error) -> None:
        self.description = description
        self.publish_function = publish_function
        self.on_finished = on_finished
        self.on_error = on_error
        self.progress_reporter = _FakeTaskReporter()
        self.progressChanged = _FakeSignal()


@pytest.fixture
def in_qgis(monkeypatch) -> list[_FakeTask]:
    """Pretend to run inside QGIS, recording the tasks started."""
    tasks: list[_FakeTask] = []

    def _start(description, publish_function, on_finished, on_error):
        tasks.append(_FakeTask(description, publish_function, on_finished, on_error))
        return tasks[-1]

    fake_module = types.ModuleType("dicogis.publishing.qgis_task")
    fake_module.start_publish_task = _start
    monkeypatch.setitem(sys.modules, "dicogis.publishing.qgis_task", fake_module)
    monkeypatch.setattr(
        "dicogis.ui.mw_dicogis.qgis_application_is_running", lambda: True
    )
    monkeypatch.setattr(
        "dicogis.ui.wdg_tab_publish.qgis_application_is_running", lambda: True
    )
    monkeypatch.setattr("dicogis.utils.http.qgis_application_is_running", lambda: True)
    return tasks


# #############################################################################
# ########## Checks tests ##########
# ##################################


def test_check_needs_a_folder(window, errors):
    window.wdg_tab_publish.set_input_folder("")

    assert window.check_fields(tab_data_type=3) is False
    assert errors


def test_check_udata_needs_its_key(window, errors):
    window.wdg_tab_publish.set_publish_target("udata")
    window.wdg_tab_publish.lne_udata_api_key.setText("")

    assert window.check_fields(tab_data_type=3) is False
    assert "uData" in errors[0]


def test_check_udata_ignores_the_geonetwork_fields(window, errors):
    window.wdg_tab_publish.set_publish_target("udata")
    window.wdg_tab_publish.lne_udata_api_key.setText("key")

    assert window.check_fields(tab_data_type=3) is True
    assert not errors


@pytest.mark.parametrize(
    ("widget_name", "value", "expected"),
    [
        ("lne_geonetwork_url_base", "", "URL"),
        ("lne_geonetwork_group", "", "group"),
        ("lne_geonetwork_group", "editors", "group"),
        ("lne_geonetwork_username", "", "username"),
        ("lne_geonetwork_password", "", "password"),
    ],
)
def test_check_geonetwork_fields(window, errors, widget_name, value, expected):
    _fill_geonetwork(window)
    getattr(window.wdg_tab_publish, widget_name).setText(value)

    assert window.check_fields(tab_data_type=3) is False
    assert expected in errors[0]


def test_check_geonetwork_complete(window, errors):
    _fill_geonetwork(window)

    assert window.check_fields(tab_data_type=3) is True
    assert not errors


@pytest.mark.usefixtures("in_qgis")
def test_check_geonetwork_authcfg_replaces_the_account(qtbot, errors, tmp_path):
    main_window = DicoGIS()
    qtbot.addWidget(main_window)
    _fill_geonetwork(main_window)
    tab = main_window.wdg_tab_publish
    tab.set_input_folder(str(tmp_path))
    tab.lne_geonetwork_username.setText("")
    tab.lne_geonetwork_password.setText("")
    tab.lne_geonetwork_authcfg.setText("abc1234")

    assert main_window.check_fields(tab_data_type=3) is True
    assert not errors


# #############################################################################
# ########## Dispatch tests ########
# ##################################


def test_publication_of_the_selected_catalog(window):
    _fill_geonetwork(window)
    tab = window.wdg_tab_publish
    tab.lne_geonetwork_portal.setText("inspire")
    tab.lne_geonetwork_categories.setText("1,3")
    tab._set_geonetwork_update_mode("complete")
    tab.cbx_geonetwork_reject_if_invalid.setChecked(True)

    publication = window._prepare_publication()

    assert publication.func is geonetwork.publish_metadata_folder
    assert publication.keywords["input_folder"] == Path(tab.get_input_folder())
    assert publication.keywords["url_base"] == "https://gn.example/geonetwork"
    assert publication.keywords["group"] == "2"
    assert publication.keywords["credentials"].username == "editor"
    assert publication.keywords["credentials"].password == "s3cret"  # noqa: S105
    assert publication.keywords["portal"] == "inspire"
    assert publication.keywords["categories"] == ["1", "3"]
    assert publication.keywords["update_mode"] == "complete"
    assert publication.keywords["reject_if_invalid"] is True

    tab.set_publish_target("udata")
    assert window._prepare_publication().func is udata.publish_metadata_folder


def test_outside_qgis_it_runs_in_a_thread(window, monkeypatch, qtbot):
    _fill_geonetwork(window)
    received = {}
    expected_report = PublishReport(published=1)

    def _fake_publish(**kwargs):
        received.update(kwargs)
        return expected_report

    monkeypatch.setattr(window, "_prepare_publication", lambda: partial(_fake_publish))
    finished = []
    monkeypatch.setattr(window, "_on_publish_finished", finished.append)

    window.process_publish()

    assert window._publish_task is None
    assert window._proc_thread is not None
    qtbot.waitUntil(lambda: finished == [expected_report], timeout=5000)
    qtbot.waitUntil(lambda: window._proc_thread is None, timeout=5000)
    assert received["progress_reporter"] is window._progress_reporter


def test_inside_qgis_it_runs_in_a_task(window, in_qgis):
    _fill_geonetwork(window)

    window.process_publish()

    assert len(in_qgis) == 1
    assert window._proc_thread is None
    task = in_qgis[0]
    assert window._publish_task is task
    # the cancel button acts on what's running
    assert window._progress_reporter is task.progress_reporter
    assert task.on_error == window._on_processing_error
    assert window._on_publish_task_progress in task.progressChanged.slots


def test_task_gets_a_client_with_authcfg_and_feedback(window, in_qgis, monkeypatch):
    _fill_geonetwork(window)
    window.wdg_tab_publish.lne_geonetwork_authcfg.setText("abc1234")
    window.wdg_tab_publish.lne_geonetwork_username.setText("")
    received = {}

    def _fake_publish(**kwargs):
        received.update(kwargs)
        return PublishReport()

    monkeypatch.setattr(window, "_prepare_publication", lambda: partial(_fake_publish))

    window.process_publish()
    reporter, feedback = object(), object()
    in_qgis[0].publish_function(reporter, feedback)

    assert received["progress_reporter"] is reporter
    assert isinstance(received["http_client"], QgisHttpClient)
    assert received["http_client"].authcfg == "abc1234"
    assert received["http_client"].feedback is feedback


def test_authcfg_means_no_credentials(window, in_qgis):
    _fill_geonetwork(window)
    window.wdg_tab_publish.lne_geonetwork_authcfg.setText("abc1234")
    window.wdg_tab_publish.lbl_geonetwork_authcfg.setVisible(True)

    assert in_qgis == []
    assert window._prepare_publication().keywords["credentials"] is None


def test_task_for_udata_does_not_take_the_authcfg(window, in_qgis, monkeypatch):
    window.wdg_tab_publish.set_publish_target("udata")
    window.wdg_tab_publish.lne_geonetwork_authcfg.setText("abc1234")
    received = {}

    def _fake_publish(**kwargs):
        received.update(kwargs)
        return PublishReport()

    monkeypatch.setattr(window, "_prepare_publication", lambda: partial(_fake_publish))

    window.process_publish()
    in_qgis[0].publish_function(object(), object())

    assert received["http_client"].authcfg is None


def test_outside_qgis_the_default_client_is_requests(window):
    from dicogis.utils.http import get_http_client

    assert isinstance(get_http_client(), RequestsHttpClient)
    assert window._publish_task is None


def test_task_progress(window):
    window._on_publish_task_progress(42.5)

    assert window.prg_layers.maximum() == 100
    assert window.prg_layers.value() == 42


def test_end_of_a_run_drops_the_task(window, in_qgis):
    _fill_geonetwork(window)
    window.process_publish()
    assert window._publish_task is not None

    window._on_publish_finished(PublishReport(published=1))

    assert window._publish_task is None
    # QGIS deletes the task: closing the window must not try to cancel it
    assert window._progress_reporter is None
    assert in_qgis


def test_cancel_button_cancels_the_task(window, in_qgis):
    _fill_geonetwork(window)
    window.process_publish()

    window._on_cancel_clicked()

    assert in_qgis[0].progress_reporter.cancel_requested is True


def test_canceled_run_is_told(window):
    window._on_publish_finished(PublishReport(published=1, canceled=True))

    assert "1 published" in window.lbl_status.text()
    assert "cancel" in window.lbl_status.text().lower()


def test_up_to_date_records_are_told(window):
    window._on_publish_finished(PublishReport(up_to_date=3))

    assert "3 already complete" in window.lbl_status.text()


def test_iso19139_export_prefills_the_publish_tab(window, tmp_path):
    window.serializer = MetadatasetSerializerIso19139(
        settings=CatalogRecordSettings(),
        localized_strings={},
        output_path=tmp_path / "iso",
    )
    window.wdg_tab_publish.set_input_folder("")
    window.wdg_tab_publish.set_publish_target("udata")

    window._prefill_publish_input_folder()

    assert window.wdg_tab_publish.get_publish_target() == "geonetwork"
    assert window.wdg_tab_publish.get_input_folder().endswith("iso")


def test_excel_export_leaves_the_publish_tab_alone(window, tmp_path):
    window.serializer = types.SimpleNamespace(output_path=tmp_path / "out.xlsx")
    window.wdg_tab_publish.set_input_folder("untouched")
    window.wdg_tab_publish.set_publish_target("geonetwork")

    window._prefill_publish_input_folder()

    assert window.wdg_tab_publish.get_input_folder() == "untouched"
    assert window.wdg_tab_publish.get_publish_target() == "geonetwork"
