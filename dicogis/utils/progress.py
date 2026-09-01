#! python3  # noqa: E265


"""
Name:         Progress
Purpose:      Toolkit-agnostic contract used by the processing pipeline to
              report progress and to be told to stop.

Author:       Julien Moura (@geojulien)
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# Standard library
from typing import Protocol, runtime_checkable


# ##############################################################################
# ############ Classes ############
# #################################


class OperationCanceled(Exception):
    """Raised by the processing pipeline when its progress reporter asked it
    to stop. Distinct from a real error: the operation didn't fail, a caller
    (typically an end-user hitting a cancel button) interrupted it."""


@runtime_checkable
class ProgressReporter(Protocol):
    """Toolkit-agnostic contract for reporting processing progress and for
    letting the caller interrupt it.

    Kept free of any Qt/GDAL import on purpose: it's implemented by the PyQt6
    GUI (dicogis.ui.workers.QtProgressReporter), it's passed as None by
    dicogis-cli, and it's what a QGIS plugin would implement on top of
    QgsTask.setProgress()/QgsTask.isCanceled(). Which is also why it lives
    here rather than next to the pipeline that consumes it: importing it from
    dicogis.georeaders.process_files would drag GDAL in (see that module's
    imports), and dicogis.listing must stay importable without GDAL.
    """

    def set_message(self, message: str) -> None:
        """Update the currently displayed status message."""
        ...

    def increment(self, amount: int = 1) -> None:
        """Increment the progress counter."""
        ...

    def set_total(self, total: int) -> None:
        """Set the total/maximum value of the progress counter."""
        ...

    def is_canceled(self) -> bool:
        """Whether the running operation has been asked to stop.

        Polled cooperatively by the pipeline: implementations must be cheap
        and safe to call from any thread, since the parallel folder scan
        calls it from its worker threads.
        """
        ...


# ##############################################################################
# ########## Functions #############
# ##################################


def raise_if_canceled(progress_reporter: ProgressReporter | None) -> None:
    """Raise OperationCanceled if the reporter asked the operation to stop.

    Args:
        progress_reporter: reporter to poll. None (e.g. from dicogis-cli,
            which has nothing to cancel with) never cancels.

    Raises:
        OperationCanceled: if the reporter reports a cancellation request.
    """
    if progress_reporter is not None and progress_reporter.is_canceled():
        raise OperationCanceled()
