#! python3

"""
Tests for the Qt workers and the QtProgressReporter signal contract.

Usage from the repo root folder:
    pytest tests/ui/test_workers.py
"""

# #############################################################################
# ########## Libraries #############
# ##################################

# package
from dicogis.cli.cmd_publish import PublishReport
from dicogis.ui.workers import FolderScanWorker, PublishWorker, QtProgressReporter
from dicogis.utils.progress import OperationCanceled, ProgressReporter

# #############################################################################
# ########## Tests ##################
# ##################################


def test_qt_progress_reporter_signals(qtbot):
    reporter = QtProgressReporter()

    with qtbot.waitSignal(reporter.message_changed, timeout=1000) as blocker:
        reporter.set_message("hello")
    assert blocker.args == ["hello"]

    with qtbot.waitSignal(reporter.total_changed, timeout=1000) as blocker:
        reporter.set_total(42)
    assert blocker.args == [42]

    with qtbot.waitSignal(reporter.progress_incremented, timeout=1000) as blocker:
        reporter.increment()
    assert blocker.args == [1]

    with qtbot.waitSignal(reporter.progress_incremented, timeout=1000) as blocker:
        reporter.increment(amount=2)
    assert blocker.args == [3]


def test_folder_scan_worker_run_emits_finished(qtbot, tmp_path):
    (tmp_path / "sub").mkdir()

    worker = FolderScanWorker(target_folder=str(tmp_path))

    with qtbot.waitSignal(worker.finished, timeout=5000) as blocker:
        worker.run()

    result = blocker.args[0]
    assert isinstance(result, tuple)
    # first element is the number of folders parsed
    assert result[0] == 1


def test_qt_progress_reporter_satisfies_the_protocol(qtbot):
    """It's what the core pipeline is typed against, and what a QGIS plugin
    would mirror on top of QgsTask."""
    assert isinstance(QtProgressReporter(), ProgressReporter)


def test_qt_progress_reporter_cancellation_flag(qtbot):
    reporter = QtProgressReporter()

    assert reporter.is_canceled() is False

    reporter.request_cancel()

    assert reporter.is_canceled() is True


def test_folder_scan_worker_emits_canceled_instead_of_error(qtbot, monkeypatch):
    """A cancellation is not a failure: it must reach the GUI through its own
    signal, so the user doesn't get an error dialog for something they asked
    for."""

    def _canceled(**kwargs):
        raise OperationCanceled()

    monkeypatch.setattr("dicogis.ui.workers.find_geodata_files", _canceled)

    worker = FolderScanWorker(target_folder="/does/not/matter")
    errors = []
    worker.error.connect(errors.append)

    with qtbot.waitSignal(worker.canceled, timeout=5000):
        worker.run()

    assert errors == []


def test_folder_scan_worker_forwards_progress_reporter(qtbot, monkeypatch):
    captured = {}

    def fake_find_geodata_files(**kwargs):
        captured.update(kwargs)
        return (0,) + ((),) * 6 + ([],) + ((),) + ([],) + ((),) * 7

    monkeypatch.setattr(
        "dicogis.ui.workers.find_geodata_files", fake_find_geodata_files
    )
    reporter = QtProgressReporter()

    worker = FolderScanWorker(
        target_folder="/does/not/matter", progress_reporter=reporter
    )

    with qtbot.waitSignal(worker.finished, timeout=5000):
        worker.run()

    assert captured["progress_reporter"] is reporter


def test_folder_scan_worker_forwards_parallel_scan_and_max_workers(qtbot, monkeypatch):
    captured = {}

    def fake_find_geodata_files(**kwargs):
        captured.update(kwargs)
        return (0,) + ((),) * 6 + ([],) + ((),) + ([],) + ((),) * 7

    monkeypatch.setattr(
        "dicogis.ui.workers.find_geodata_files", fake_find_geodata_files
    )

    worker = FolderScanWorker(
        target_folder="/does/not/matter", parallel_scan=True, max_workers=7
    )

    with qtbot.waitSignal(worker.finished, timeout=5000):
        worker.run()

    assert captured == {
        "start_folder": "/does/not/matter",
        "parallel_scan": True,
        "max_workers": 7,
        "progress_reporter": None,
    }


def test_folder_scan_worker_defaults_to_sequential_scan(qtbot, monkeypatch):
    """Off by default: matches find_geodata_files()' own default (see its
    docstring for why parallel scan isn't the default)."""
    captured = {}

    def fake_find_geodata_files(**kwargs):
        captured.update(kwargs)
        return (0,) + ((),) * 6 + ([],) + ((),) + ([],) + ((),) * 7

    monkeypatch.setattr(
        "dicogis.ui.workers.find_geodata_files", fake_find_geodata_files
    )

    worker = FolderScanWorker(target_folder="/does/not/matter")

    with qtbot.waitSignal(worker.finished, timeout=5000):
        worker.run()

    assert captured["parallel_scan"] is False
    assert captured["max_workers"] is None


def test_folder_scan_worker_run_emits_error_on_failure(qtbot, monkeypatch):
    # **kwargs, not a fixed signature: the worker passes parallel_scan/
    # max_workers/progress_reporter too, and a signature mismatch here would
    # make this test pass on a TypeError rather than on the raised error
    def _boom(**kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("dicogis.ui.workers.find_geodata_files", _boom)

    worker = FolderScanWorker(target_folder="/does/not/matter")

    with qtbot.waitSignal(worker.error, timeout=5000) as blocker:
        worker.run()

    assert "boom" in blocker.args[0]


def test_publish_worker_run_emits_finished(qtbot, tmp_path, monkeypatch):
    expected_report = PublishReport(published=2, ignored=1, failed=0)

    def _fake_publish_metadata_folder(**kwargs):
        kwargs["progress_callback"](1, 3, tmp_path / "a.json")
        kwargs["progress_callback"](3, 3, tmp_path / "c.json")
        return expected_report

    monkeypatch.setattr(
        "dicogis.ui.workers.publish_metadata_folder", _fake_publish_metadata_folder
    )

    worker = PublishWorker(
        input_folder=tmp_path,
        udata_api_key="fake-api-key",
        udata_api_url_base="https://udata-test.example/api/",
        udata_api_version="1",
    )

    progress_updates = []
    worker.progress_changed.connect(
        lambda done, total: progress_updates.append((done, total))
    )

    with qtbot.waitSignal(worker.finished, timeout=5000) as blocker:
        worker.run()

    assert blocker.args[0] is expected_report
    assert progress_updates == [(1, 3), (3, 3)]


def test_publish_worker_run_emits_error_on_failure(qtbot, tmp_path, monkeypatch):
    def _boom(**kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("dicogis.ui.workers.publish_metadata_folder", _boom)

    worker = PublishWorker(
        input_folder=tmp_path,
        udata_api_key="fake-api-key",
        udata_api_url_base="https://udata-test.example/api/",
        udata_api_version="1",
    )

    with qtbot.waitSignal(worker.error, timeout=5000) as blocker:
        worker.run()

    assert "boom" in blocker.args[0]
