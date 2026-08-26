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
from dicogis.ui.workers import FolderScanWorker, QtProgressReporter

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
