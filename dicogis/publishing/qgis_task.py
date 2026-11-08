#! python3  # noqa: E265

"""Run a publication in a QgsTask: how QGIS expects long operations to run.

Imports QGIS: to be imported only once running inside QGIS. Out of dicogis.ui, whose
modules reach Qt and QGIS through dicogis.ui.qt_compat only.
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# Standard library
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

# 3rd party
from qgis.core import QgsApplication, QgsFeedback, QgsTask

# project
from dicogis.publishing.report import PublishReport


if TYPE_CHECKING:
    from collections.abc import Callable

    from dicogis.utils.progress import ProgressReporter


# ##############################################################################
# ############ Globals ############
# #################################

logger = logging.getLogger(__name__)

# ##############################################################################
# ########## Classes ###############
# ##################################


class TaskProgressReporter:
    """ProgressReporter on top of QgsTask.setProgress() and QgsTask.isCanceled()."""

    def __init__(self, task: QgsTask) -> None:
        """Bind the reporter to its task.

        Args:
            task: running task
        """
        self.task = task
        self._total = 0
        self._count = 0

    def set_message(self, message: str) -> None:
        """Log the message: the task manager only shows the task's description."""
        logger.debug(message)

    def set_total(self, total: int) -> None:
        """Set the total value of the progress counter."""
        self._total = total

    def increment(self, amount: int = 1) -> None:
        """Increment the progress counter, as a percentage for the task manager."""
        self._count += amount
        if self._total:
            self.task.setProgress(100.0 * self._count / self._total)

    def is_canceled(self) -> bool:
        """Whether the task has been asked to stop."""
        return self.task.isCanceled()

    def request_cancel(self) -> None:
        """Ask the task to stop, like the cancel button of the task manager."""
        self.task.cancel()


class PublishTask(QgsTask):
    """Runs a publication in the background of QGIS."""

    def __init__(
        self,
        description: str,
        publish_function: Callable[[ProgressReporter, QgsFeedback], PublishReport],
        on_finished: Callable[[PublishReport], None],
        on_error: Callable[[str], None],
    ) -> None:
        """Prepare the task.

        Args:
            description: what the task manager shows
            publish_function: runs the publication, with a progress reporter and a
                feedback interrupting the running request when canceled
            on_finished: called in the main thread with the report
            on_error: called in the main thread with the error message
        """
        super().__init__(description)
        self.publish_function = publish_function
        self.on_finished = on_finished
        self.on_error = on_error
        self.progress_reporter = TaskProgressReporter(self)
        self.feedback = QgsFeedback()
        self.report: PublishReport | None = None
        self.error_message: str | None = None

    def run(self) -> bool:
        """Run the publication, in the thread of the task: no widget allowed here.

        Returns:
            True if the publication ran to its end or was canceled along the way
        """
        try:
            self.report = self.publish_function(self.progress_reporter, self.feedback)
        except Exception as err:
            logger.error(f"Publication failed. Trace: {err}")
            self.error_message = str(err)
            return False
        return True

    def cancel(self) -> None:
        """Interrupt the running request too, instead of waiting for its end."""
        self.feedback.cancel()
        super().cancel()

    def finished(self, result: bool) -> None:
        """Tell the outcome, in the main thread.

        Args:
            result: what run() returned, False if it was canceled before starting
        """
        if self.error_message is not None:
            self.on_error(self.error_message)
        elif result and self.report is not None:
            self.on_finished(self.report)
        else:
            self.on_finished(PublishReport(canceled=True))


# ##############################################################################
# ########## Functions #############
# ##################################


def start_publish_task(
    description: str,
    publish_function: Callable[[ProgressReporter, QgsFeedback], PublishReport],
    on_finished: Callable[[PublishReport], None],
    on_error: Callable[[str], None],
) -> PublishTask:
    """Hand a publication over to the task manager of QGIS.

    Args:
        description: what the task manager shows
        publish_function: see PublishTask
        on_finished: see PublishTask
        on_error: see PublishTask

    Returns:
        the task, a reference to keep as long as it's running
    """
    task = PublishTask(description, publish_function, on_finished, on_error)
    QgsApplication.taskManager().addTask(task)
    return task
