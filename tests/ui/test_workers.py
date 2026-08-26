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


def test_folder_scan_worker_run_emits_error_on_failure(qtbot, monkeypatch):
    def _boom(start_folder):
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
