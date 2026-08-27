#! python3  # noqa: E265

from pathlib import Path

from PyQt6 import uic
from PyQt6.QtWidgets import QTableWidgetItem, QWidget

from dicogis.utils.texts import TextsManager
from dicogis.utils.utils import Utilities


class ScrollableTable(QWidget):
    """
    A scrollable table with two columns in read-only mode.

    Attributes:
        table (QTableWidget): The table widget displaying key/value rows.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        localized_strings: dict | None = None,
    ):
        """Initialize the ScrollableTable widget.

        Args:
            parent: the parent widget.
            localized_strings: translated strings. Defaults to None.
        """
        super().__init__(parent)
        uic.loadUi(
            Utilities().resolve_internal_path(
                internal_path=Path("ui/wdg_scrollable_table.ui")
            ),
            self,
        )

        # handle empty localized strings
        self.localized_strings = localized_strings
        if self.localized_strings is None:
            self.localized_strings = TextsManager().load_texts()

        self.table.setHorizontalHeaderLabels(
            [
                self.localized_strings.get("key", "Key"),
                self.localized_strings.get("value", "Value"),
            ]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)

    def add_row(self, key: str, value: str) -> None:
        """Append a key/value row to the table.

        Args:
            key: value for the first column.
            value: value for the second column.
        """
        row_index = self.table.rowCount()
        self.table.insertRow(row_index)
        self.table.setItem(row_index, 0, QTableWidgetItem(str(key)))
        self.table.setItem(row_index, 1, QTableWidgetItem(str(value)))
