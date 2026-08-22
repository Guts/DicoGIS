#! python3  # noqa: E265


"""
Name:         Workers
Purpose:      QThread-based workers running long tasks off the GUI thread, plus a
              Qt-signal-based implementation of the ProgressReporter protocol.

Author:       Julien Moura (@geojulien)
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import logging
from pathlib import Path

# 3rd party
from PyQt6.QtCore import QObject, pyqtSignal

# project
from dicogis.export.base_serializer import MetadatasetSerializerBase
from dicogis.georeaders.process_files import ProcessingFiles, ProgressReporter
from dicogis.georeaders.read_postgis import ReadPostGIS
from dicogis.listing.geodata_listing import find_geodata_files

# ##############################################################################
# ############ Globals ############
# #################################

logger = logging.getLogger(__name__)

# ##############################################################################
# ########## Classes ###############
# ##################################


class QtProgressReporter(QObject):
    """Qt-signal-based implementation of the ProgressReporter protocol.

    Safe to instanciate and drive from a worker thread: signals emitted here are
    delivered to slots connected from the GUI thread through Qt's automatic
    cross-thread queued connections.
    """

    message_changed = pyqtSignal(str)
    progress_incremented = pyqtSignal(int)
    total_changed = pyqtSignal(int)

    def __init__(self, parent: QObject | None = None) -> None:
        """Initialize the progress reporter."""
        super().__init__(parent)
        self._count = 0

    def set_message(self, message: str) -> None:
        """Update the currently displayed status message."""
        self.message_changed.emit(message)

    def increment(self, amount: int = 1) -> None:
        """Increment the progress counter."""
        self._count += amount
        self.progress_incremented.emit(self._count)

    def set_total(self, total: int) -> None:
        """Set the total/maximum value of the progress counter."""
        self.total_changed.emit(total)


class FolderScanWorker(QObject):
    """Worker listing geodata files under a folder structure, off the GUI thread."""

    status_message = pyqtSignal(str)
    finished = pyqtSignal(tuple)
    error = pyqtSignal(str)

    def __init__(self, target_folder: str | Path, parent: QObject | None = None) -> None:
        """Initialize the worker.

        Args:
            target_folder: folder to walk into to look for geographic datasets.
            parent: Qt parent object.
        """
        super().__init__(parent)
        self.target_folder = target_folder

    def run(self) -> None:
        """Run the folder scan and emit the resulting lists of files."""
        try:
            self.status_message.emit(f"Scanning: {self.target_folder}")
            result = find_geodata_files(start_folder=self.target_folder)
            self.finished.emit(result)
        except Exception as err:
            logger.error(f"Folder scan failed. Trace: {err}")
            self.error.emit(str(err))


class ProcessingWorker(QObject):
    """Worker processing a queue of geodata files, off the GUI thread."""

    finished = pyqtSignal(int)
    error = pyqtSignal(str)

    def __init__(
        self, processor: ProcessingFiles, parent: QObject | None = None
    ) -> None:
        """Initialize the worker.

        Args:
            processor: pre-configured files processor to run.
            parent: Qt parent object.
        """
        super().__init__(parent)
        self.processor = processor

    def run(self) -> None:
        """Run the files processing and emit the total number of files processed."""
        try:
            self.processor.process_datasets_in_queue()
            self.finished.emit(self.processor.total_files or 0)
        except Exception as err:
            logger.error(f"Files processing failed. Trace: {err}")
            self.error.emit(str(err))


class PostgisProcessingWorker(QObject):
    """Worker processing PostGIS tables/views, off the GUI thread."""

    finished = pyqtSignal(int)
    error = pyqtSignal(str)

    def __init__(
        self,
        sgbd_reader: ReadPostGIS,
        serializer: MetadatasetSerializerBase,
        progress_reporter: ProgressReporter | None = None,
        parent: QObject | None = None,
    ) -> None:
        """Initialize the worker.

        Args:
            sgbd_reader: pre-connected PostGIS reader.
            serializer: output serializer to write metadata into.
            progress_reporter: progress reporter to notify. Defaults to None.
            parent: Qt parent object.
        """
        super().__init__(parent)
        self.sgbd_reader = sgbd_reader
        self.serializer = serializer
        self.progress_reporter = progress_reporter

    def run(self) -> None:
        """Iterate over PostGIS layers, serialize their metadata and emit progress."""
        try:
            total_layers = self.sgbd_reader.conn.GetLayerCount()
            if self.progress_reporter is not None:
                self.progress_reporter.set_total(total_layers)

            for idx_layer in range(total_layers):
                layer = self.sgbd_reader.conn.GetLayerByIndex(idx_layer)
                if self.progress_reporter is not None:
                    self.progress_reporter.set_message(f"Reading: {layer.GetName()}")
                metadataset = self.sgbd_reader.infos_dataset(layer)
                logger.debug(f"Table examined: {metadataset.name}")
                self.serializer.serialize_metadaset(metadataset=metadataset)
                logger.debug(
                    f"Layer metadata stored into workbook: {metadataset.name}"
                )
                if self.progress_reporter is not None:
                    self.progress_reporter.increment()

            self.serializer.post_serializing()
            self.finished.emit(total_layers)
        except Exception as err:
            logger.error(f"PostGIS processing failed. Trace: {err}")
            self.error.emit(str(err))
