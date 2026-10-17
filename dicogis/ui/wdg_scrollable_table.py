#! python3  # noqa: E265

from pathlib import Path

from dicogis.ui.qt_compat import uic
from dicogis.ui.qt_compat.QtWidgets import QTableWidgetItem, QWidget
from dicogis.utils.utils import Utilities


class ScrollableTable(QWidget):
    """
    A scrollable table with two columns in read-only mode.

    Attributes:
        tbw_content (QTableWidget): The table widget displaying key/value rows.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
    ):
        """Initialize the ScrollableTable widget.

        Args:
            parent: the parent widget.
        """
        super().__init__(parent)
        uic.loadUi(
            Utilities().resolve_internal_path(
                internal_path=Path("ui/wdg_scrollable_table.ui")
            ),
            self,
        )

        self.tbw_content.setHorizontalHeaderLabels(
            [
                self.tr("Key"),
                self.tr("Value"),
            ]
        )
        self.tbw_content.verticalHeader().setVisible(False)
        self.tbw_content.horizontalHeader().setStretchLastSection(True)

    def add_row(self, key: str, value: str) -> None:
        """Append a key/value row to the table.

        Args:
            key: value for the first column.
            value: value for the second column.
        """
        row_index = self.tbw_content.rowCount()
        self.tbw_content.insertRow(row_index)
        self.tbw_content.setItem(row_index, 0, QTableWidgetItem(str(key)))
        self.tbw_content.setItem(row_index, 1, QTableWidgetItem(str(value)))
