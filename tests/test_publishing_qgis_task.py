#! python3  # noqa: E265

"""
Tests for dicogis.publishing.qgis_task, with a fake qgis.core: its integration with the
real task manager runs in the QGIS job of the integration workflow.

Usage from the repo root folder:
    pytest tests/test_publishing_qgis_task.py
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# standard library
import importlib
import subprocess
import sys
import types

# 3rd party
import pytest

# project
from dicogis.publishing.report import PublishReport


# ##############################################################################
# ########## Classes ###############
# ##################################


class _FakeTask:
    """Stands in for QgsTask, with what the code under test relies on."""

    def __init__(self, description="") -> None:
        self.description = description
        self.progress = None
        self.canceled = False

    def setProgress(self, progress) -> None:
        self.progress = progress

    def isCanceled(self) -> bool:
        return self.canceled

    def cancel(self) -> None:
        self.canceled = True


class _FakeFeedback:
    def __init__(self) -> None:
        self.canceled = False

    def cancel(self) -> None:
        self.canceled = True


class _FakeTaskManager:
    def __init__(self) -> None:
        self.tasks = []

    def addTask(self, task) -> None:
        self.tasks.append(task)


# ##############################################################################
# ########## Fixtures ##############
# ##################################


@pytest.fixture
def qgis_task(monkeypatch):
    """Import dicogis.publishing.qgis_task against a fake qgis.core."""
    task_manager = _FakeTaskManager()
    fake_core = types.ModuleType("qgis.core")
    fake_core.QgsTask = _FakeTask
    fake_core.QgsFeedback = _FakeFeedback
    fake_core.QgsApplication = types.SimpleNamespace(taskManager=lambda: task_manager)
    monkeypatch.setitem(sys.modules, "qgis", types.ModuleType("qgis"))
    monkeypatch.setitem(sys.modules, "qgis.core", fake_core)
    monkeypatch.delitem(sys.modules, "dicogis.publishing.qgis_task", raising=False)
    module = importlib.import_module("dicogis.publishing.qgis_task")
    yield module, task_manager
    sys.modules.pop("dicogis.publishing.qgis_task", None)


# ##############################################################################
# ########## Tests ##################
# ##################################


def test_publication_runs_in_the_task_and_reports_in_finished(qgis_task):
    module, task_manager = qgis_task
    expected_report = PublishReport(published=1)
    finished, errors, received = [], [], []

    def _publish(progress_reporter, feedback):
        received.append((progress_reporter, feedback))
        return expected_report

    task = module.start_publish_task(
        "Publishing", _publish, finished.append, errors.append
    )

    assert task_manager.tasks == [task]
    assert finished == []  # nothing runs before the task manager starts it

    assert task.run() is True
    task.finished(True)

    assert received == [(task.progress_reporter, task.feedback)]
    assert finished == [expected_report]
    assert errors == []


def test_failure_is_told_by_finished(qgis_task):
    module, _ = qgis_task
    finished, errors = [], []

    def _boom(progress_reporter, feedback):
        raise RuntimeError("boom")

    task = module.PublishTask("Publishing", _boom, finished.append, errors.append)

    assert task.run() is False
    task.finished(False)

    assert errors == ["boom"]
    assert finished == []


def test_canceled_before_starting_gives_an_empty_canceled_report(qgis_task):
    module, _ = qgis_task
    finished, errors = [], []
    task = module.PublishTask("Publishing", None, finished.append, errors.append)

    task.finished(False)

    assert len(finished) == 1
    assert finished[0].canceled is True
    assert errors == []


def test_cancel_interrupts_the_running_request(qgis_task):
    module, _ = qgis_task
    task = module.PublishTask("Publishing", None, None, None)

    task.progress_reporter.request_cancel()

    assert task.feedback.canceled is True
    assert task.isCanceled() is True
    assert task.progress_reporter.is_canceled() is True


def test_progress_is_a_percentage(qgis_task):
    module, _ = qgis_task
    task = module.PublishTask("Publishing", None, None, None)
    reporter = task.progress_reporter

    reporter.increment()
    assert task.progress is None  # total unknown: nothing to tell yet

    reporter.set_total(4)
    reporter.increment()

    assert task.progress == pytest.approx(50.0)


def test_core_packages_do_not_import_it():
    """It needs QGIS, which the publication code must do without."""
    code = (
        "import sys; import dicogis.publishing.geonetwork, dicogis.publishing.udata; "
        "print('dicogis.publishing.qgis_task' in sys.modules, 'qgis.core' in sys.modules)"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )

    assert result.stdout.strip() == "False False"


# ##############################################################################
# ##### Stand alone program ########
# ##################################
if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
